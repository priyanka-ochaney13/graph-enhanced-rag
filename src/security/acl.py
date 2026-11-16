def user_can_access(doc_acl: list[str], user_roles: list[str]) -> bool:
    if not doc_acl:
        return False
    return any(role in user_roles for role in doc_acl)


def qdrant_acl_filter(user_roles: list[str]):
    from qdrant_client.models import Filter, FieldCondition, MatchAny
    return Filter(
        must=[
            FieldCondition(
                key="allowed_roles",
                match=MatchAny(any=user_roles),
            )
        ]
    )