from rainbows.bootstrap import bootstrapping_metadata
import ntpath

# 1) Get the app folder.
app_path = ntpath.join(ntpath.dirname(__file__), "..", "..", "app")

# 2) Check the app folder exists.
if ntpath.isdir(app_path):
    # 3) Check if "models" exists. If so, add it.
    models_path = ntpath.join(app_path, "models")
    if ntpath.isdir(models_path):
        bootstrapping_metadata.set_models_path(models_path)

    # 4) Check if "views" exists. If so, add it.
    views_path = ntpath.join(app_path, "views")
    if ntpath.isdir(views_path):
        bootstrapping_metadata.set_views_path(views_path)

    # 5) Check if "controllers" exists. If so, add it.
    controllers_path = ntpath.join(app_path, "controllers")
    if ntpath.isdir(controllers_path):
        bootstrapping_metadata.set_controllers_path(controllers_path)

    # 6) Check if "helpers" exists. If so, add it.
    helpers_path = ntpath.join(app_path, "helpers")
    if ntpath.isdir(helpers_path):
        bootstrapping_metadata.set_helpers_path(helpers_path)

    # 6) Check if "services" exists. If so, add it.
    services_path = ntpath.join(app_path, "services")
    if ntpath.isdir(services_path):
        bootstrapping_metadata.set_services_path(services_path)
