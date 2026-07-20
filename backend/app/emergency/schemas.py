from pydantic import BaseModel


class EmergencyTopic(BaseModel):
    slug: str
    title: str
    immediate_action: str
    instructions: list[str]
    do_not: list[str]
    call_now_if: list[str]


class EmergencyConfig(BaseModel):
    emergency_number: str
    country_hint: str
    disclaimer: str
    topics: list[EmergencyTopic]
