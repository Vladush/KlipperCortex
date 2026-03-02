cmake_minimum_required(VERSION 3.16)
project(KlipperCortex C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Configure IREE build for a bare-metal runtime
# We only need the runtime, not the compiler or tests.
set(IREE_BUILD_COMPILER OFF CACHE BOOL "" FORCE)
set(IREE_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(IREE_BUILD_SAMPLES OFF CACHE BOOL "" FORCE)
set(IREE_BUILD_BENCHMARKS OFF CACHE BOOL "" FORCE)
set(BENCHMARK_ENABLE_TESTING OFF CACHE BOOL "" FORCE)

# Bypass try_run checks for Google Benchmark when cross-compiling
set(HAVE_STD_REGEX ON CACHE BOOL "" FORCE)
set(HAVE_POSIX_REGEX ON CACHE BOOL "" FORCE)

set(IREE_ENABLE_WERROR OFF CACHE BOOL "Disable strict Werror during cross-compilation" FORCE)

# Force-disable all -Werror behavior across all submodules (including ukernels)
add_compile_options(-Wno-error -Wno-shift-count-overflow -Wno-pointer-to-int-cast)

# Disable unsupported arm64 microkernel extensions that break cross-compilation
set(IREE_UK_BUILD_ARM_64_FULLFP16 OFF CACHE BOOL "" FORCE)
set(IREE_UK_BUILD_ARM_64_FP16FML OFF CACHE BOOL "" FORCE)
set(IREE_UK_BUILD_ARM_64_BF16 OFF CACHE BOOL "" FORCE)
set(IREE_UK_BUILD_ARM_64_DOTPROD OFF CACHE BOOL "" FORCE)
set(IREE_UK_BUILD_ARM_64_I8MM OFF CACHE BOOL "" FORCE)

# Enable local execution drivers (sync + multi-threaded task)
set(IREE_HAL_DRIVER_DEFAULTS OFF CACHE BOOL "" FORCE)
set(IREE_HAL_DRIVER_LOCAL_SYNC ON CACHE BOOL "" FORCE)
set(IREE_HAL_DRIVER_LOCAL_TASK ON CACHE BOOL "" FORCE)

# Include standard modules used by IREE builtins
include(CheckCSourceCompiles)
include(CheckCXXSourceCompiles)

# Add IREE as a subproject
add_subdirectory(third_party/iree)

# Executable
add_executable(model_runner src/model_runner.cpp)

# Setup includes using IREE's targets
target_include_directories(model_runner PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/iree/runtime/src
)

target_compile_definitions(model_runner PRIVATE
    IREE_ALLOCATOR_SYSTEM_CTL=iree_allocator_libc_ctl
)

# Link against IREE runtime unified and core drivers
target_link_libraries(model_runner
    PRIVATE
    iree_runtime_unified
    iree_hal_drivers_local_sync_sync_driver
    iree_hal_drivers_local_task_task_driver
)
