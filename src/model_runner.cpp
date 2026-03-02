// Note: This C++ runner was created as a lightweight, dependency-free
// alternative to the Python inference_loop.py. It avoids the memory overhead
// and installation complexity of the Python iree-runtime bindings on the
// Raspberry Pi (Cortex-A53), ensuring minimum latency for hardware-level
// execution.

#include <algorithm>
#include <cstring>
#include <fcntl.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

#include "iree/base/api.h"
#include "iree/hal/api.h"
#include "iree/runtime/api.h"

class PmrBuffer {
public:
  explicit PmrBuffer(std::size_t size) : buffer_(size) {}
  std::uint8_t *data() { return buffer_.data(); }
  const std::uint8_t *data() const { return buffer_.data(); }
  std::size_t size() const { return buffer_.size(); }

private:
  std::vector<std::uint8_t> buffer_;
};

class IreeModel {
public:
  explicit IreeModel(const std::filesystem::path &model_path)
      : instance_(NULL), session_(NULL) {
    if (!std::filesystem::exists(model_path)) {
      throw std::runtime_error("Model file not found: " + model_path.string());
    }

    // Initialize IREE instance
    iree_runtime_instance_options_t instance_options;
    iree_runtime_instance_options_initialize(&instance_options);
    iree_runtime_instance_options_use_all_available_drivers(&instance_options);
    IREE_CHECK_OK(iree_runtime_instance_create(
        &instance_options, iree_allocator_system(), &instance_));

    // Create session (local-sync driver for CPU by default)
    iree_hal_device_t *device = NULL;
    IREE_CHECK_OK(iree_runtime_instance_try_create_default_device(
        instance_, iree_make_cstring_view("local-sync"), &device));

    iree_runtime_session_options_t session_options;
    iree_runtime_session_options_initialize(&session_options);
    IREE_CHECK_OK(iree_runtime_session_create_with_device(
        instance_, &session_options, device,
        iree_runtime_instance_host_allocator(instance_), &session_));
    iree_hal_device_release(device);

    // Load bytecode module from file
    IREE_CHECK_OK(iree_runtime_session_append_bytecode_module_from_file(
        session_, model_path.c_str()));

    // Resolve 'predict' function
    IREE_CHECK_OK(iree_runtime_session_lookup_function(
        session_, iree_make_cstring_view("module.predict"), &predict_fn_));
  }

  ~IreeModel() {
    iree_runtime_session_release(session_);
    iree_runtime_instance_release(instance_);
  }

  bool run(const PmrBuffer &input, PmrBuffer &output) {
    iree_runtime_call_t call;
    IREE_CHECK_OK(iree_runtime_call_initialize(session_, predict_fn_, &call));

    // Wrap input data (assuming 224x224x3 float32)
    iree_hal_dim_t shape[] = {1, 224, 224, 3};
    iree_hal_buffer_view_t *input_view = NULL;
    IREE_CHECK_OK(iree_hal_buffer_view_allocate_buffer_copy(
        iree_runtime_session_device(session_),
        iree_runtime_session_device_allocator(session_), IREE_ARRAYSIZE(shape),
        shape, IREE_HAL_ELEMENT_TYPE_FLOAT_32,
        IREE_HAL_ENCODING_TYPE_DENSE_ROW_MAJOR,
        (iree_hal_buffer_params_t){
            .usage = IREE_HAL_BUFFER_USAGE_DEFAULT,
            .access = IREE_HAL_MEMORY_ACCESS_ALL,
            .type = IREE_HAL_MEMORY_TYPE_DEVICE_LOCAL,
        },
        iree_make_const_byte_span(input.data(), input.size()), &input_view));

    IREE_CHECK_OK(
        iree_runtime_call_inputs_push_back_buffer_view(&call, input_view));
    iree_hal_buffer_view_release(input_view);

    // Invoke
    IREE_CHECK_OK(iree_runtime_call_invoke(&call, /*flags=*/0));

    // Get output (assumes index 1 is 'spaghetti' label per inference_loop.py)
    iree_hal_buffer_view_t *output_view = NULL;
    IREE_CHECK_OK(
        iree_runtime_call_outputs_pop_front_buffer_view(&call, &output_view));

    // Copy result back to host
    IREE_CHECK_OK(iree_hal_device_transfer_d2h(
        iree_runtime_session_device(session_),
        iree_hal_buffer_view_buffer(output_view), 0, output.data(),
        std::min(output.size(),
                 (std::size_t)iree_hal_buffer_view_byte_length(output_view)),
        IREE_HAL_TRANSFER_BUFFER_FLAG_DEFAULT, iree_infinite_timeout()));

    iree_hal_buffer_view_release(output_view);
    iree_runtime_call_deinitialize(&call);
    return true;
  }

private:
  iree_runtime_instance_t *instance_;
  iree_runtime_session_t *session_;
  iree_vm_function_t predict_fn_;
};

int main(int argc, char *argv[]) {
  if (argc != 3) {
    std::cerr << "Usage: " << std::filesystem::path(argv[0]).filename()
              << " <model.vmfb> <input.bin>\n";
    return EXIT_FAILURE;
  }

  const std::filesystem::path model_path = argv[1];
  const std::filesystem::path input_path = argv[2];

  std::ifstream in(input_path, std::ios::binary | std::ios::ate);
  if (!in) {
    std::cerr << "Failed to open input file: " << input_path << '\n';
    return EXIT_FAILURE;
  }
  std::size_t input_size = static_cast<std::size_t>(in.tellg());
  in.seekg(0);
  PmrBuffer input_buf(input_size);
  in.read(reinterpret_cast<char *>(input_buf.data()), input_size);

  // Result buffer (assuming 2 floats for background/spaghetti)
  PmrBuffer output_buf(2 * sizeof(float));

  try {
    IreeModel model(model_path);
    if (model.run(input_buf, output_buf)) {
      float *results = reinterpret_cast<float *>(output_buf.data());
      std::cout << "Background score: " << results[0] << "\n";
      std::cout << "Spaghetti score: " << results[1] << "\n";
    }
  } catch (const std::exception &e) {
    std::cerr << "Error: " << e.what() << '\n';
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
