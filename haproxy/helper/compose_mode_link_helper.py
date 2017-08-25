import logging
import compose_mode_helper as ComposeModeHelper

logger = logging.getLogger("haproxy")


def get_compose_mode_links(docker, haproxy_container):
    labels = haproxy_container.get("Config", {}).get("Labels", {})
    project = labels.get("com.docker.compose.project", "")
    if not project:
        raise Exception("Cannot read compose labels. Are you using docker compose V2?")

    networks = haproxy_container.get("NetworkSettings", {}).get("Networks", {})
    linked_compose_services = _get_linked_compose_services(networks, project)

    links = ComposeModeHelper._calc_links(docker, linked_compose_services, project)
    return links, set(["%s_%s" % (project, service) for service in linked_compose_services])


def get_additional_links(docker, additional_services):
    links = {}
    services = set()
    for additional_service in additional_services.split(","):
        terms = additional_service.strip().split(":")
        if len(terms) == 2:
            project = terms[0]
            service = terms[1]
            link = ComposeModeHelper._calc_links(docker, [service], project)
            if link:
                links.update(link)
                services.add("%s_%s" % (project, service))
            else:
                logger.info("Cannot find the additional service: %s" % additional_service.strip())
    return links, services


def _get_linked_compose_services(networks, project):
    prefix = "%s_" % project
    prefix_len = len(prefix)

    haproxy_links = []
    for network in networks.itervalues():
        network_links = network.get("Links", [])
        if network_links:
            haproxy_links.extend(network_links)

    linked_services = []
    for link in haproxy_links:
        terms = link.strip().split(":")
        service = terms[0].strip()
        if service and service.startswith(prefix):
            last = service.rfind("_")
            linked_service = service[prefix_len:last]
            if linked_service not in linked_services:
                linked_services.append(linked_service)
    return linked_services
