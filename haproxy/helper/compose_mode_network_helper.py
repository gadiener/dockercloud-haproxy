import logging
import compose_mode_helper as ComposeModeHelper

logger = logging.getLogger("haproxy")


def get_compose_mode_networks(docker, haproxy_container):
    networks = _find_container_networks_ids(haproxy_container, docker.networks())
    
    labels = haproxy_container.get("Config", {}).get("Labels", {})
    project = labels.get("com.docker.compose.project", "")
    linked_compose_services = []
    cleaned_haproxy_name = _clean_container_name(project, haproxy_container['Name'].lstrip("/"), 1)

    for network in networks:
        containers_in_network = _find_container_in_network(project, network)

        for container in containers_in_network:
            if container != cleaned_haproxy_name and container not in linked_compose_services:
                linked_compose_services.append(container)
    
    links = ComposeModeHelper._calc_links(docker, linked_compose_services, project)

    return links, set(["%s_%s" % (project, service) for service in linked_compose_services])


def _find_container_networks_ids(container, networks_data):
    network_filtered = []

    for network in networks_data:
        if container['Id'] in network['Containers'] and network['Id'] not in network_filtered:
            network_filtered.append(network)
    return network_filtered


def _find_container_in_network(project, network):
    services_names = []
    
    if network:
        for container_id in network['Containers']:
            name = _clean_container_name(project, network['Containers'][container_id]['Name'])
            if name:
                services_names.append(name)
    return services_names


def _clean_container_name(project, name, aa=0):
    prefix = "%s_" % project
    prefix_len = len(prefix)

    terms = name.strip().split(":")
    service = terms[0].strip()
        
    if service and service.startswith(prefix):
        last = service.rfind("_")
        return service[prefix_len:last]
    else:
        return None
