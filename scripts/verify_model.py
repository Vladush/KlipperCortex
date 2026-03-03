import numpy as np
import iree.runtime as ireert
import sys


def main():
    print("Loading IREE module...")
    try:
        config = ireert.Config("local-sync")
        with open("models/spaghetti_host.vmfb", "rb") as f:
            vmfb_data = f.read()
            if len(vmfb_data) == 0:
                print("Error: VMFB file is empty!")
                sys.exit(1)
            vmfb = ireert.VmModule.from_flatbuffer(config.vm_instance, vmfb_data)

        print(f"Module functions: {vmfb.function_names}")

        ctx = ireert.SystemContext(config=config)
        ctx.add_vm_module(vmfb)

        # Access the bound module using its name (defaults to 'module')
        module = ctx.modules.module

        func_name = "main"
        if "predict" in vmfb.function_names:
            func_name = "predict"

        print(f"Using entry point: {func_name}")
        predict_fn = module[func_name]

        # Create random input (Batch=1, H=224, W=224, C=3)
        input_data = np.random.rand(1, 224, 224, 3).astype(np.float32)

        print("Running inference...")
        result = predict_fn(input_data)

        # Result might be a tuple or single tensor
        if isinstance(result, tuple):
            result = result[0]  # Take first output if multiple

        output = result.to_host()
        print(f"Success! Output shape: {output.shape}")
        print(f"Sample output values: {output.flatten()[:5]}")

    except Exception as e:
        print(f"Verification Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
