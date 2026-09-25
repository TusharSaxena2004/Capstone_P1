from ml_core.llm_client import call_local_llm

prompt = '''Analyze if these two eyewitness claims contradict each other.
Claim 1: The getaway car was a red sedan.
Claim 2: The getaway car was a blue SUV.
Return strict JSON:
{"contradiction": true, "rationale": "One witness stated the car was a red sedan while another stated it was a blue SUV."}'''

print(call_local_llm(prompt))
