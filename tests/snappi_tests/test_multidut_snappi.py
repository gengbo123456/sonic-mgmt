import time
import pytest
import random
import logging
from tests.common.helpers.assertions import pytest_assert
from tests.common.fixtures.conn_graph_facts import conn_graph_facts, fanout_graph_facts_multidut, \
    fanout_graph_facts                                                                              # noqa: F401
from tests.common.snappi_tests.snappi_fixtures import snappi_api_serv_ip, snappi_api_serv_port, \
    get_snappi_ports_single_dut, snappi_testbed_config, snappi_dut_base_config, \
    get_snappi_ports_multi_dut, is_snappi_multidut, tgen_port_info, \
    snappi_api, get_snappi_ports, snappi_port_selection, get_snappi_ports_for_rdma, cleanup_config  # noqa: F401
from tests.common.snappi_tests.port import select_ports
from tests.common.snappi_tests.qos_fixtures import prio_dscp_map, lossless_prio_list                # noqa: F401
from tests.common.snappi_tests.snappi_helpers import wait_for_arp
from tests.common.snappi_tests.snappi_fixtures import gen_data_flow_dest_ip
logger = logging.getLogger(__name__)
SNAPPI_POLL_DELAY_SEC = 2

pytestmark = [pytest.mark.topology('multidut-tgen')]


@pytest.mark.disable_loganalyzer
def __gen_all_to_all_traffic(testbed_config,
                             duthosts,
                             port_config_list,
                             conn_data,
                             fanout_data,
                             priority,
                             prio_dscp_map              # noqa: F811
                             ):

    line_rate = 100
    if duthosts[0].facts['asic_type'] == "cisco-8000":
        line_rate = 50
    rate_percent = line_rate / (len(port_config_list) - 1)

    duration_sec = 2
    pkt_size = 1024

    tx_port_id_list, rx_port_id_list = select_ports(port_config_list=port_config_list,
                                                    pattern="all to all",
                                                    rx_port_id=0)
    for tx_port_id in tx_port_id_list:
        for rx_port_id in rx_port_id_list:
            if tx_port_id == rx_port_id:
                continue

            tx_port_config = next((x for x in port_config_list if x.id == tx_port_id), None)
            rx_port_config = next((x for x in port_config_list if x.id == rx_port_id), None)
            tx_mac = tx_port_config.mac
            if tx_port_config.gateway == rx_port_config.gateway and \
               tx_port_config.prefix_len == rx_port_config.prefix_len:
                """ If soruce and destination port are in the same subnet """
                rx_mac = rx_port_config.mac
            else:
                rx_mac = tx_port_config.gateway_mac

            tx_port_name = testbed_config.ports[tx_port_id].name
            rx_port_name = testbed_config.ports[rx_port_id].name

            flow = testbed_config.flows.flow(
                name="Flow {} -> {}".format(tx_port_id, rx_port_id))[-1]

            flow.tx_rx.port.tx_name = tx_port_name
            flow.tx_rx.port.rx_name = rx_port_name

            eth, ipv4, udp = flow.packet.ethernet().ipv4().udp()
            src_port = random.randint(5000, 6000)
            udp.src_port.increment.start = src_port
            udp.src_port.increment.step = 1
            udp.src_port.increment.count = 1

            eth.src.value = tx_mac
            eth.dst.value = rx_mac
            eth.pfc_queue.value = priority

            ipv4.src.value = tx_port_config.ip
            ipv4.dst.value = gen_data_flow_dest_ip(rx_port_config.ip)
            ipv4.priority.choice = ipv4.priority.DSCP
            ipv4.priority.dscp.phb.values = prio_dscp_map[priority]
            ipv4.priority.dscp.ecn.value = (
                ipv4.priority.dscp.ecn.CAPABLE_TRANSPORT_1
            )

            flow.size.fixed = pkt_size
            flow.rate.percentage = rate_percent
            flow.duration.fixed_seconds.seconds = duration_sec

            flow.metrics.enable = True
            flow.metrics.loss = True

    return testbed_config


@pytest.fixture(autouse=True, scope='module')
def number_of_tx_rx_ports():
    yield (1, 1)


def test_snappi(request,
                duthosts,
                snappi_api,                   # noqa: F811
                conn_graph_facts,             # noqa: F811
                fanout_graph_facts_multidut,  # noqa: F811
                lossless_prio_list,           # noqa: F811
                get_snappi_ports,             # noqa: F811
                tbinfo,
                prio_dscp_map,                # noqa: F811
                number_of_tx_rx_ports,        # noqa: F811
                tgen_port_info,               # noqa: F811
                ):

    """
    Test if we can use Snappi API to generate traffic in a testbed

    Args:
        snappi_api (pytest fixture): Snappi session
        snappi_testbed_config (pytest fixture): testbed configuration information
        conn_graph_facts (pytest fixture): connection graph
        fanout_graph_facts_multidut (pytest fixture): fanout graph
        prio_dscp_map (pytest fixture): priority vs. DSCP map (key = priority)
        tbinfo (pytest fixture): fixture provides information about testbed
        get_snappi_ports (pytest fixture): gets snappi ports and connected DUT port info and returns as a list
    Returns:
        N/A
    """
    testbed_config, port_config_list, snappi_ports = tgen_port_info
    for port in snappi_ports:
        logger.info('Snappi ports selected for test:{}'.format(port['peer_port']))

    lossless_prio = random.sample(lossless_prio_list, 1)
    lossless_prio = int(lossless_prio[0])

    config = __gen_all_to_all_traffic(testbed_config=testbed_config,
                                      port_config_list=port_config_list,
                                      conn_data=conn_graph_facts,
                                      fanout_data=fanout_graph_facts_multidut,
                                      priority=int(lossless_prio),
                                      prio_dscp_map=prio_dscp_map,
                                      duthosts=duthosts)

    pkt_size = config.flows[0].size.fixed
    rate_percent = config.flows[0].rate.percentage
    duration_sec = config.flows[0].duration.fixed_seconds.seconds

    port_speed = config.layer1[0].speed
    words = port_speed.split('_')
    pytest_assert(len(words) == 3 and words[1].isdigit(),
                  'Fail to get port speed from {}'.format(port_speed))

    port_speed_gbps = int(words[1])

    # """ Apply configuration """
    snappi_api.set_config(config)

    # """Wait for Arp"""
    wait_for_arp(snappi_api, max_attempts=30, poll_interval_sec=2)

    # """ Start traffic """
    cs = snappi_api.control_state()
    cs.traffic.flow_transmit.state = cs.traffic.flow_transmit.START
    snappi_api.set_control_state(cs)

    # """ Wait for traffic to finish """
    time.sleep(duration_sec)

    attempts = 0
    max_attempts = 20
    all_flow_names = [flow.name for flow in config.flows]

    while attempts < max_attempts:
        request = snappi_api.metrics_request()
        request.flow.flow_names = all_flow_names
        rows = snappi_api.get_metrics(request).flow_metrics

        """ If all the data flows have stopped """
        transmit_states = [row.transmit for row in rows]
        if len(rows) == len(all_flow_names) and\
           list(set(transmit_states)) == ['stopped']:
            time.sleep(2)
            break
        else:
            time.sleep(1)
            attempts += 1

    pytest_assert(attempts < max_attempts,
                  "Flows do not stop in {} seconds".format(max_attempts))

    """ Dump per-flow statistics """
    request = snappi_api.metrics_request()
    request.flow.flow_names = all_flow_names
    rows = snappi_api.get_metrics(request).flow_metrics

    cs = snappi_api.control_state()
    cs.traffic.flow_transmit.state = cs.traffic.flow_transmit.STOP
    snappi_api.set_control_state(cs)

    """ Analyze traffic results """
    for row in rows:
        flow_name = row.name
        rx_frames = row.frames_rx
        tx_frames = row.frames_tx

        pytest_assert(rx_frames == tx_frames,
                      'packet losses for {} (Tx: {}, Rx: {})'.
                      format(flow_name, tx_frames, rx_frames))

        tput_bps = port_speed_gbps * 1e9 * rate_percent / 100.0
        exp_rx_frames = tput_bps * duration_sec / 8 / pkt_size

        deviation_thresh = 0.05
        ratio = float(exp_rx_frames) / rx_frames
        deviation = abs(ratio - 1)

        pytest_assert(deviation <= deviation_thresh,
                      'Expected / Actual # of pkts for flow {}: {} / {}'.
                      format(flow_name, exp_rx_frames, rx_frames))
