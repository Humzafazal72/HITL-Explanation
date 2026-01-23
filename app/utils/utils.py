import os
import json
import boto3
import socket
from typing import Any, List
from pydantic import BaseModel
from botocore.config import Config
from urllib.parse import urlparse, urlunparse
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from core.langgraph_.Workflow import workflow_hitl

TIGRIS_ENDPOINT = os.environ.get("TIGRIS_STORAGE_ENDPOINT")
TIGRIS_ACCESS_KEY = os.environ.get("TIGRIS_STORAGE_ACCESS_KEY_ID")
TIGRIS_SECRET_KEY = os.environ.get("TIGRIS_STORAGE_SECRET_ACCESS_KEY")


def sse_response(event: str, data: dict, concept_id: str):
    """
    Generate SSE compatible response for the client

    :param event: name of event
    :type event: str
    :param data: data to be sent to the client
    :type data: dict
    :param concept_id: concept id.
    :type concept_id: str
    """
    return (
        f"event: {event}\n"
        f"data: {json.dumps({'concept_id': concept_id, **data})}\n\n"
    )


def to_json_safe(obj: Any):
    """
    Convert any obj to json compatible dict.

    :param obj: object to be made compatible.
    :type obj: Any
    """
    if isinstance(obj, BaseModel):
        return obj.model_dump()

    elif isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [to_json_safe(v) for v in obj]

    return obj


async def get_graph():
    """initiate the langgraph graph and create the sqlite checkpointer"""
    postgre_conn_string = os.getenv("SUPABASE_DB_URL")
    # parsed = urlparse(original_conn_string)

    # print(parsed)
    # ipv4_ip = socket.getaddrinfo(parsed.hostname, None, family=socket.AF_INET)[0][4][0]
    # new_netloc = parsed.netloc.replace(parsed.hostname, ipv4_ip)
    # ipv4_conn_string = urlunparse(parsed._replace(netloc=new_netloc))

    cm = AsyncPostgresSaver.from_conn_string(postgre_conn_string)
    checkpointer = await cm.__aenter__()
    await checkpointer.setup()
    graph = workflow_hitl.compile(checkpointer=checkpointer)
    return graph, cm


def upload_diagrams(concept_id: str):
    """
    Upload the generated diagrams to Tigris/S3.

    :param concept_id: Name of the concept whose files need to be stored
    :type concept_id: str
    """
    s3_client = boto3.client(
        "s3",
        endpoint_url=TIGRIS_ENDPOINT,
        aws_access_key_id=TIGRIS_ACCESS_KEY,
        aws_secret_access_key=TIGRIS_SECRET_KEY,
        config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    )
    directory_path = os.path.join("Storage", concept_id)

    for file_name in os.listdir(directory_path):
        local_path = os.path.join(directory_path, file_name)
        bucket_name = "explanation-dev"
        target_folder = f"Diagrams/{concept_id}"
        response = s3_client.upload_file(
            local_path, bucket_name, target_folder, file_name
        )


async def add_to_explanation_db(
    explainer_output: dict,
    concept_id: int,
    concept_name: str,
    tts_data: List[str],
    snippets_data: dict,
    db: Any,
):
    """
    add explanations to the db

    :param explainer_output: Description
    :type explainer_output: dict
    :param concept_id: Description
    :type concept_id: int
    :param concept_name: Description
    :type concept_name: str
    """

    await db.execute(
        "INSERT INTO lessons(ID, name) VALUES(?,?)", (concept_id, concept_name)
    )
    await db.execute(
        "INSERT INTO conclusions(lesson_id, conclusion_text) VALUES(?,?)",
        (concept_id, explainer_output["conclusion"]),
    )
    await db.execute(
        "INSERT INTO contexts(lesson_id, context_text) VALUES(?,?)",
        (concept_id, explainer_output["context"]),
    )

    # insert explanation steps one by one
    for step_num, step_text in enumerate(explainer_output["steps"]):
        await db.execute(
            "INSERT INTO explanation_steps(lesson_id, step_num, step_text) VALUES(?,?,?)",
            (concept_id, step_num, step_text),
        )

    # insert TTS steps one by one
    for tts_num, tts_text in enumerate(tts_data):
        await db.execute(
            "INSERT INTO tts_steps(lesson_id, tts_text, step_num) VALUES(?,?,?)",
            (concept_id,  tts_text, tts_num)
        )
    
    # insert context snippets
    for snippet_num,snippet_text in enumerate(snippets_data["context_snippets"]):
        await db.execute(
            "INSERT INTO context_snippets(lesson_id, snippet_text, snippet_num) VALUES(?,?,?)",
            (concept_id, snippet_text, snippet_num)
        )

    # insert conlusion snippets
    for snippet_num,snippet_text in enumerate(snippets_data["conclusion_snippets"]):
        await db.execute(
            "INSERT INTO conclusion_snippets(lesson_id, snippet_text, snippet_num) VALUES(?,?,?)",
            (concept_id, snippet_text, snippet_num)
        )
    
    #insert explanation steps snippets
    for step_num,snippet_lists in enumerate(snippets_data["step_snippets"]):
        for snippet_num,snippet_text in enumerate(snippet_lists):
            await db.execute(
                "INSERT INTO step_snippets(lesson_id, step_num, snippet_num, snippet_text) VALUES(?,?,?,?)",
                (concept_id, step_num, snippet_num, snippet_text)
            )