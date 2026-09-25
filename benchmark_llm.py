import time
from ml_core.llm_client import call_local_llm

prompt = "Extract subject and action: The car jumped the red light."
t0 = time.time()
print("Sending prompt to LM Studio...")
res = call_local_llm(prompt)
print(f"Response received in {time.time() - t0:.2f} seconds:")
print(res)
