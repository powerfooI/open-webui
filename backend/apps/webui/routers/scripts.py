from fastapi import (
    Depends,
    HTTPException,
    status,
    UploadFile,
    Request,
)


from datetime import datetime, timedelta
from typing import List, Union, Optional
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse

from pydantic import BaseModel
import json

from apps.webui.models.scripts import (
    Scripts,
    ScriptForm,
    ScriptModel,
    ScriptBrief,
    ListScriptResponse,
)
from utils.utils import get_verified_user, get_admin_user
from constants import ERROR_MESSAGES

import os
import uuid
import os, shutil, logging

from config import SRC_LOG_LEVELS, UPLOAD_DIR


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])


router = APIRouter()

############################
# Create Script
############################


@router.post("/", response_model=Optional[ScriptModel])
async def create_new_script(
    request: Request, form_data: ScriptForm, user=Depends(get_verified_user)
):
    script = Scripts.get_script_by_name(form_data.name, user_id=user.id)
    if script == None:
        try:
            script = Scripts.insert_new_script(user.id, form_data)
            if script:
                return script
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ERROR_MESSAGES.DEFAULT("Error creating script"),
                )
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT(e),
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.NAME_TAG_TAKEN,
        )


############################
# List Scripts
############################


@router.get("/", response_model=ListScriptResponse)
async def list_scripts(request: Request, user=Depends(get_verified_user)):
    kwargs = {}
    limit = request.query_params.get("limit")
    offset = request.query_params.get("offset")
    if limit:
        kwargs["limit"] = limit
    if offset:
        kwargs["offset"] = offset
    name_like = request.query_params.get("name_like")
    if name_like:
        kwargs["name_like"] = name_like
    if user.role == "admin":
        return Scripts.list_scripts(**kwargs)
    else:
        kwargs["user_id"] = user.id
        return Scripts.list_scripts(**kwargs)


############################
# Update Script By Id
############################


@router.post("/{id}", response_model=Optional[ScriptModel])
async def update_script_by_id(
    request: Request, id: str, form_data: ScriptForm, user=Depends(get_verified_user)
):
    try:
        updated = {**form_data.model_dump()}
        if user.role == "admin":
            script = Scripts.update_script_by_id(id, updated)
        else:
            script = Scripts.update_script_by_id(id, updated, user_id=user.id)
        if script:
            return script
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error updating script"),
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# Get Script By Id
############################


@router.get("/{id}", response_model=Optional[ScriptModel])
async def get_script_by_id(id: str, user=Depends(get_verified_user)):
    if user.role == "admin":
        script = Scripts.get_script_by_id(id)
    else:
        script = Scripts.get_script_by_id(id, user_id=user.id)

    if script:
        return script
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# Delete Script By Id
############################


@router.delete("/{id}")
async def delete_script_by_id(id: str, user=Depends(get_verified_user)):
    if user.role == "admin":
        script = Scripts.get_script_by_id(id)
    else:
        script = Scripts.get_script_by_id(id, user_id=user.id)

    if script:
        result = Scripts.delete_script_by_id(id, user_id=user.id)
        if result:
            return {"message": "Script deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error deleting file"),
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )
