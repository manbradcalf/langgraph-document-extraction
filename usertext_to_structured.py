from outputs.data_models.settlement_agreement import SettlementAgreement
from pprint import pprint
from config import openai_client
from inputs.openai_models import models

# Setup
openAI_model = models[1]
system_prompt = "Extract the following fields from the user text."
user_prompt = """
        ACME Corp will pay $12,500 to Medcalf Software Solutions starting 2025-10-01.
        Terms: net 30, early termination requires 15 days notice.
"""

result = openai_client.responses.parse(
    model="gpt-4.1",  # or another model that supports Structured Outputs
    input=[
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": user_prompt,
        },
    ],
    text_format=SettlementAgreement,
)

if result.output_parsed is not None:
    contract: SettlementAgreement = result.output_parsed
    pprint(contract)
else:
    print("Unable to Parse PDF")
