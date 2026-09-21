def all_routers():
    """Every router module registers here; imported lazily to avoid import cycles."""
    routers = []
    for name in ROUTER_MODULES:
        module = __import__(f"app.routers.{name}", fromlist=["router"])
        routers.append(module.router)
    return routers


ROUTER_MODULES: list[str] = ["auth", "admin_orgs", "users", "classes", "taxonomy", "topics", "tags", "assets", "questions", "documents", "ai_models", "org_settings", "review"]
