def _calc_links(docker, linked_compose_services, project):
    links = {}
    for _container in docker.containers():
        container_id = _container.get("Id", "")
        container = docker.inspect_container(container_id)
        compose_labels = container.get("Config", {}).get("Labels", {})
        compose_project = compose_labels.get("com.docker.compose.project", "")
        compose_service = compose_labels.get("com.docker.compose.service", "")

        if compose_project == project and compose_service in linked_compose_services:
            service_name = "%s_%s" % (compose_project, compose_service)
            container_name = container.get("Name").lstrip("/")
            container_evvvars = get_container_envvars(container)
            endpoints = get_container_endpoints(container, container_name)
            links[container_id] = {"service_name": service_name,
                                   "container_envvars": container_evvvars,
                                   "container_name": container_name,
                                   "endpoints": endpoints,
                                   "compose_service": compose_service,
                                   "compose_project": compose_project}
    return links


def get_container_envvars(container):
    container_evvvars = []
    envvars = container.get("Config", {}).get("Env", [])
    for envvar in envvars:
        terms = envvar.split("=", 1)
        container_evvvar = {"key": terms[0]}
        if len(terms) == 2:
            container_evvvar["value"] = terms[1]
        else:
            container_evvvar["value"] = ""
        container_evvvars.append(container_evvvar)
    return container_evvvars


def get_container_endpoints(container, container_name):
    endpoints = {}
    container_endpoints = container.get("Config", {}).get("ExposedPorts", {})
    for k, v in container_endpoints.iteritems():
        if k:
            terms = k.split("/", 1)
            port = terms[0]
            if len(terms) == 2:
                protocol = terms[1]
            else:
                protocol = "tcp"
            if not v:
                v = "%s://%s:%s" % (protocol, container_name, port)
            endpoints[k] = v
    return endpoints


def get_service_links_str(links):
    return sorted(set([link.get("service_name") for link in links.itervalues()]))


def get_container_links_str(haproxy_links):
    return sorted(set([link.get("container_name") for link in haproxy_links.itervalues()]))
