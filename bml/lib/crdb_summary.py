from util import date_valid
from util import longest_scenario_test_name
from util import connect_crdb


def time_summary(config, days):
    uuids = get_uuids_list(config, days)
    padding = longest_scenario_test_name(config)
    conn = connect_crdb(config)
    cur = conn.cursor()
    table_name = config['table_name'][0]
    for uuid in uuids:
        cur.execute("select test, osp_version, avg_runtime , \
                    grade, timestamp from {} \
                    where uuid = '{}'".format(table_name, uuid))
        rows = cur.fetchall()
        output_string = ""
        for row in rows:
            output_string += row[0].ljust(padding) + " " +  \
                "%06.2f" %float(row[2]) + "     " + str(row[3]) + "\n"
            osp_version = row[1]
        header = ("Browbeat UUID: " + uuid + " OSP_version: " + osp_version + "\n")
        header += ("".ljust(80, "-")) + "\n"
        output_string = header + output_string
        print output_string


def get_uuids_list(config, days):
    conn = connect_crdb(config)
    cur = conn.cursor()
    table_name = config['table_name'][0]
    cur.execute("select uuid, timestamp from {}".format(table_name))  # noqa
    rows = cur.fetchall()
    uuid_list = set()
    for row in rows:
        uuid = row[0]
        if date_valid(row[1], days):
            if uuid not in uuid_list:
                uuid_list.add(uuid)
    return uuid_list
