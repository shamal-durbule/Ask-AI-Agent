from fastapi import Request


def get_workspace_id(request: Request) -> str:
    """Simple auth stub: reads workspace ID from header, defaults to 'default'.

    In production, this would validate a JWT or session token and extract
    the workspace/organization ID. For this assignment, it's a pass-through
    that identifies the current workspace for query scoping.
    """
    return request.headers.get("X-Workspace-Id", "default")
