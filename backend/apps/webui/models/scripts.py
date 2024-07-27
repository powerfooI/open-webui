from pydantic import BaseModel
from typing import List, Optional
import time
import logging
from uuid import uuid4

from sqlalchemy import Column, String, Text, BigInteger, Boolean

from apps.webui.internal.db import JSONField, Base, get_db
from apps.webui.models.users import Users

from config import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# Python Scripts DB Schema
####################


class Script(Base):
    __tablename__ = "script"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    name = Column(Text)
    content = Column(Text)
    meta = Column(JSONField)
    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)


class Meta(BaseModel):
    description: Optional[str] = None
    manifest: Optional[dict] = {}


class ScriptBrief(BaseModel):
    """
    ScriptBrief is a brief representation of a script, used in lists
    """

    id: str
    name: str
    user_id: str
    meta: Meta
    updated_at: int
    created_at: int


class ScriptModel(ScriptBrief):
    """
    ScriptModel extends ScriptBrief with content field
    """

    content: str


####################
# Forms
####################


class ScriptForm(BaseModel):
    name: str
    content: str
    meta: Meta


def script_to_model(script: Script) -> ScriptModel:
    return ScriptModel(
        id=script.id,
        user_id=script.user_id,
        name=script.name,
        content=script.content,
        meta=script.meta,
        updated_at=script.updated_at,
        created_at=script.created_at,
    )


def script_to_brief(script: Script) -> ScriptBrief:
    return ScriptBrief(
        id=script.id,
        name=script.name,
        user_id=script.user_id,
        meta=script.meta,
        updated_at=script.updated_at,
        created_at=script.created_at,
    )


class ScriptsTable:
    def insert_new_script(
        self, user_id: str, form_data: ScriptForm
    ) -> Optional[ScriptModel]:
        script = ScriptModel(
            **{
                **form_data.model_dump(),
                "user_id": user_id,
                "updated_at": int(time.time()),
                "created_at": int(time.time()),
                "id": str(uuid4()),
            }
        )

        try:
            with get_db() as db:
                result = Script(**script.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                if result:
                    return script_to_model(result)
                else:
                    return None
        except Exception as e:
            print(f"Error creating script: {e}")
            return None

    def list_users_scripts(self, user_id: str, **kwargs) -> List[ScriptBrief]:
        filters = []
        with get_db() as db:
            return [
                script_to_brief(script)
                for script in db.query(Script).filter_by(user_id=user_id).all()
            ]

    def get_script_by_name(
        self, name: str, **kwargs,
    ) -> Optional[ScriptModel]:
        filters = [Script.name==name]
        if kwargs.get("user_id"):
            filters.append(Script.user_id == kwargs.get("user_id"))
        try:
            with get_db() as db:
                script = db.query(Script).filter(*filters).first()
                if script is None:
                    return None
                return script_to_model(script)
        except:
            return None

    def get_users_script_by_id(self, user_id: str, id: str) -> Optional[ScriptModel]:
        try:
            with get_db() as db:
                script = db.query(Script).filter_by(user_id=user_id, id=id).first()
                return script_to_model(script)
        except:
            return None

    def update_users_script_by_id(
        self, user_id: str, id: str, updated: dict
    ) -> Optional[ScriptModel]:
        with get_db() as db:
            try:
                db.query(Script).filter_by(user_id=user_id, id=id).update(
                    {
                        **updated,
                        "updated_at": int(time.time()),
                    }
                )
                db.commit()
                return self.get_users_script_by_id(user_id, id)
            except:
                return None

    def delete_users_script_by_id(self, user_id: str, id: str) -> bool:
        with get_db() as db:
            try:
                db.query(Script).filter_by(user_id=user_id, id=id).delete()
                db.commit()

                return True
            except:
                return False

    # Admin methods

    def list_scripts(self, **kwargs) -> List[ScriptBrief]:
        filters = []
        if kwargs.get("user_id"):
            filters.append(Script.user_id == kwargs.get("user_id"))
        if kwargs.get("name_like"):
            filters.append(Script.name.like(f"{kwargs.get('name_like')}%"))
        with get_db() as db:
            return [
                script_to_brief(script)
                for script in db.query(Script).filter(*filters).all()
            ]

    def get_script_by_id(self, id: str, **kwargs) -> Optional[ScriptModel]:
        filters = [Script.id == id]
        if kwargs.get("user_id"):
            filters.append(Script.user_id == kwargs.get("user_id"))
        try:
            with get_db() as db:
                script = db.query(Script).filter(*filters).first()
                if script is None:
                    return None
                return script_to_model(script)
        except:
            return None

    def update_script_by_id(
        self, id: str, updated: dict, **kwargs
    ) -> Optional[ScriptModel]:
        filters = [Script.id == id]
        if kwargs.get("user_id"):
            filters.append(Script.user_id == kwargs.get("user_id"))
        with get_db() as db:
            try:
                db.query(Script).filter(*filters).update(
                    {
                        **updated,
                        "updated_at": int(time.time()),
                    }
                )
                db.commit()
                return self.get_script_by_id(id)
            except:
                return None

    def delete_script_by_id(self, id: str, **kwargs) -> bool:
        filters = [Script.id == id]
        if kwargs.get("user_id"):
            filters.append(Script.user_id == kwargs.get("user_id"))
        with get_db() as db:
            try:
                db.query(Script).filter(*filters).delete()
                db.commit()
                return True
            except:
                return False


Scripts = ScriptsTable()
