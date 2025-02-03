import typing as t
import pydantic

T = t.TypeVar("T")


class BaseFields:
    class _RecordIdField(pydantic.BaseModel):
        type: str
        text: str

    class _PersonField(pydantic.BaseModel):
        name: str
        id: str
        en_name: str
        email: str

    class GroupChatField(pydantic.BaseModel):
        name: str
        avatar_url: str
        id: str

    class LinkField(pydantic.BaseModel):
        text: str
        link: str

    class _AttachmentField(pydantic.BaseModel):
        file_token: str
        name: str
        type: str
        size: int
        url: str
        tmp_url: str

    class LocationField(pydantic.BaseModel):
        location: str
        pname: str
        cityname: str
        adname: str
        address: str
        name: str
        full_address: str

    AttachmentField = t.List[_AttachmentField]
    MultilineField = str
    BarcodeField = str
    NumberField = str
    CurrencyField = str
    ProgressField = str
    RatingField = str
    SingleOptionField = str
    MultipleOptionsField = t.List[str]
    DateField = int
    CheckboxField = bool
    PersonField = t.List[_PersonField]
    RecordIdType = t.List[_RecordIdField]
    TextField = str

    model_config = pydantic.ConfigDict(ignored_types=(int,))
