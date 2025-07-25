# Transceiver Onboarding Test Plan

## Scope

This test plan outlines a comprehensive framework for ensuring feature parity for new transceivers being onboarded to SONiC. The goal is to automate all tests listed in this document, covering the following areas:

- **Link Behavior**: Test link behavior using shut/no shut commands and under process crash and device reboot scenarios.
- **Transceiver Information Fields**: Verify transceiver specific fields (Vendor name, part number, serial number) via CLI commands, ensuring values match expectations.
- **Firmware**: Check firmware version readability and compliance with vendor-suggested values, using regex for version pattern matching.
- **DOM Data**: Ensure Digital Optical Monitoring (DOM) data is correctly read and within acceptable ranges.
- **Flags and Alerts**: Confirm no unexpected flags (e.g., Loss of Signal (LOS), Loss of Lock (LOL), DOM warnings) are set.
- **Firmware Management**: Test firmware upgrade under various scenarios.
- **Remote Reseat**: Verify support for remote reseat functionality.

**Transceiver Specific Capabilities** (if available):

- Adjustments to frequency and tx power.
- Configuration of different Forward Error Correction (FEC) modes.
- For breakout cables, ensure specific lanes are correctly modified by shut/no shut or other lane specific commands.

**Optics Scope**:
The test plan includes various optics types, such as:

- Active Optical Cables (AOC)
- Active Electrical Cables (AEC)
- DR8 optics
- Direct Attach Cables (DAC)
- Short Range/Long Range (SR/LR) optics
- SONiC-supported breakout cables

**Optics Specifications**:
Tests will cover optics compliant with:

- CMIS
- C-CMIS
- SFF-8636
- SFF-8436
- SFF-8472

## Testbed Topology

A total of 2 ports of a device with the onboarding transceiver should be connected with a cable. Each of these ports can be on the same device or different devices as well. In the case of a breakout cable, the expectation is to connect all sides of the cable to the DUT and test each port individually.

1. Standalone topology with both ports connected on the same SONiC device (self loopback)

    ```text
    +-----------------+
    |           Port 1|<----+
    |                 |     | Loopback
    |    Device       |     | Connection
    |           Port 2|<----+
    |                 |
    +-----------------+
    ```

2. Point-to-point topology with port connected on different SONiC devices

    ```text

    +-----------------+     +-----------------+
    |           Port 1|<--->|Port 1           |
    |                 |     |                 |
    |    Device 1     |     |     Device 2    |
    |                 |     |                 |
    |                 |     |                 |
    +-----------------+     +-----------------+
    ```

3. Topology with port connected between SONiC device and 2 servers using a Y-cable

    ```text
                               +-----------------+
                               |                 |
                               |     Server 1    |
    +-----------------+        |                 |
    |                 |    +-->| Port            |
    |                 |    |   |                 |
    |   SONiC Device  |    |   +-----------------+
    |                 |<---+   +-----------------+
    |                 |    |   |                 |
    |                 |    |   |     Server 2    |
    +-----------------+    +-->| Port            |
                               |                 |
                               |                 |
                               +-----------------+
    ```

## Test Cases

### 1. Tests not involving traffic

These tests do not require traffic and are standalone, designed to run on a Device Under Test (DUT) with the transceiver plugged into 2 ports, connected by a cable.

**Breakout Cable Assumptions for the Below Tests:**

- All sides of the breakout cable should be connected to the DUT, and each port should be tested individually starting from subport 1 to subport N. The test should be run in reverse order as well i.e. starting from subport N to subport 1.
- For link toggling tests on a subport, it's crucial to ensure that the link status of remaining subports of the breakout port group remains unaffected.

**Pre-requisites for the Below Tests:**

1. A file `transceiver_dut_info.csv` (located in `ansible/files/transceiver_inventory` directory) should be present to describe the metadata of the transceiver connected to every port of each DUT. Following should be the format of the file

    ```csv
    dut_name,physical_port,vendor_pn,normalized_vendor_pn,vendor_sn,vendor_date,vendor_oui,vendor_rev
    dut_name_1,port_1,vendor_part_number,normalized_vendor_part_number,serial_number,vendor_date_code,vendor_oui,revision_number
    dut_name_1,port_2,vendor_part_number,normalized_vendor_part_number,serial_number,vendor_date_code,vendor_oui,revision_number
    # Add more DUTs as needed
    ```

    - `dut_name`: The name of the DUT.
    - `physical_port`: The physical port number on the DUT where the transceiver is connected (e.g., 1, 2, etc.).
    - `vendor_pn`: The vendor part number as specified in the transceiver's EEPROM.
    - `normalized_vendor_pn`: The normalized vendor part number, created by applying the normalization rules described in the [CMIS CDB Firmware Binary Management](#141-cmis-cdb-firmware-binary-management) section.
    - `vendor_sn`: The vendor serial number.
    - `vendor_date`: The vendor date code.
    - `vendor_oui`: The vendor OUI.
    - `vendor_rev`: The vendor revision number.

    Functionality to parse the above files and store the data in a dictionary should be implemented in the test framework. This dictionary should act as a source of truth for the test cases.
    The `normalized_vendor_pn` from `transceiver_dut_info.csv` file should be used to fetch the common attributes of the transceiver from `transceiver_common_attributes.csv` file for a given port.
    > Note: If any non-string value is planned to be added to the dictionary, the `convert_row_types` function should be modified to convert the relevant value to the appropriate datatype.

    Example of an dictionary created by parsing the above files

    ```python
    {
        "dut_name_1": {
            "port_1": {
                "vendor_date": "vendor_date_code",
                "vendor_oui": "vendor_oui",
                "vendor_rev": "revision_number",
                "vendor_sn": "serial_number",
                "vendor_pn": "vendor_part_number",
                "normalized_vendor_pn": "normalized_vendor_part_number",
                "active_firmware": "active_firmware_version",
                "inactive_firmware": "inactive_firmware_version",
                "cmis_rev": "cmis_revision",
                "vendor_name": "vendor_name",
                "normalized_vendor_name": "normalized_vendor_name",
                'vdm_supported': True,
                'cdb_backgroundmode_supported': True,
                'dual_bank_supported': True
            },
            "port_2": {
                "vendor_date": "vendor_date_code",
                "vendor_oui": "vendor_oui",
                "vendor_rev": "revision_number",
                "vendor_sn": "serial_number",
                "vendor_pn": "vendor_part_number",
                "normalized_vendor_pn": "normalized_vendor_part_number",
                "active_firmware": "active_firmware_version",
                "inactive_firmware": "inactive_firmware_version",
                "cmis_rev": "cmis_revision",
                "vendor_name": "vendor_name",
                "normalized_vendor_name": "normalized_vendor_name",
                'vdm_supported': True,
                'cdb_backgroundmode_supported': True,
                'dual_bank_supported': True
            }
        }
    }
    ```

2. A file named `transceiver_common_attributes.csv` (located in the `ansible/files/transceiver_inventory` directory) must be present to define the common attributes for each transceiver, keyed by normalized vendor part number. The file should use the following format:

    ```csv
    normalized_vendor_name,normalized_vendor_pn,active_firmware,inactive_firmware,cmis_rev,vdm_supported,cdb_backgroundmode_supported,dual_bank_supported
    <normalized_vendor_name_1>,<normalized_vendor_pn_1>,<active_firmware_version_1>,<inactive_firmware_version_1>,<cmis_revision_1>,<True or False>,<True or False>,<True or False>
    <normalized_vendor_name_2>,<normalized_vendor_pn_2>,<active_firmware_version_2>,<inactive_firmware_version_2>,<cmis_revision_2>,<True or False>,<True or False>,<True or False>
    # Add more entries as needed
    ```

    - `normalized_vendor_name`: The normalized vendor name, created by applying the normalization rules described in the [CMIS CDB Firmware Binary Management](#141-cmis-cdb-firmware-binary-management) section.
    <br>The normalization rules ensure that the vendor name is consistent and compatible with directory structures used in firmware management and upgrade tests.
    - `normalized_vendor_pn`: The normalized vendor part number, created by applying the normalization rules described in the [CMIS CDB Firmware Binary Management](#141-cmis-cdb-firmware-binary-management) section.
    <br>This ensures the inventory does not need to list every possible cable length and standardizes the format for compatibility with directory structures used in firmware management and upgrade tests. See the detailed normalization rules in the referenced section for full details.
    - `active_firmware` and `inactive_firmware`: Firmware version strings in the format `X.Y.Z` (e.g., `1.2.3`). The `active_firmware` version represents the gold firmware version.
    - `cmis_rev`: CMIS revision string in the format `X.Y`.
    - `vdm_supported`, `cdb_backgroundmode_supported`, `dual_bank_supported`: Boolean values indicating support for VDM, CDB background mode, and dual bank firmware, respectively.

3. A `transceiver_firmware_info.csv` file (located in `ansible/files/transceiver_inventory` directory) should exist if a transceiver being tested supports CMIS CDB firmware upgrade. This file will capture the firmware binary metadata for the transceiver. Each transceiver should have at least 2 firmware binaries (in addition to the gold firmware binary) so that firmware upgrade can be tested. Following should be the format of the file

    ```csv
    normalized_vendor_name,normalized_vendor_pn,fw_version,fw_binary_name,md5sum
    <normalized_vendor_name_1>,<normalized_vendor_pn_1>,<firmware_version_1>,<firmware_binary_1>,<md5sum_1>
    <normalized_vendor_name_1>,<normalized_vendor_pn_1>,<firmware_version_2>,<firmware_binary_2>,<md5sum_2>
    <normalized_vendor_name_1>,<normalized_vendor_pn_1>,<firmware_version_3>,<firmware_binary_3>,<md5sum_3>
    # Add more vendor part numbers as needed
    ```

    For each firmware binary, the following metadata should be included:

    - `normalized_vendor_name`: The normalized vendor name, created by applying the normalization rules described in the [CMIS CDB Firmware Binary Management](#141-cmis-cdb-firmware-binary-management) section.
    - `normalized_vendor_pn`: The normalized vendor part number, created by applying the normalization rules described in the [CMIS CDB Firmware Binary Management](#141-cmis-cdb-firmware-binary-management) section.
    - `fw_version`: The version of the firmware.
    - `fw_binary_name`: The filename of the firmware binary.
    - `md5sum`: The MD5 checksum of the firmware binary.

4. A `cmis_cdb_firmware_base_url.csv` file (located in `ansible/files/transceiver_inventory` directory) should be present to define the base URL for downloading CMIS CDB firmware binaries. The file should follow this format:

    ```csv
    inv_name,fw_base_url
    <inventory_file_name>,<base_url>
    ```

    - `inv_name`: The name of the inventory file that contains the definition of the target DUTs. For further details, please refer to the [Inventory File](https://github.com/sonic-net/sonic-mgmt/blob/master/docs/testbed/README.new.testbed.Configuration.md#inventory-file). The `inv_name` allows DUTs to be grouped based on their inventory file, enabling the test framework to fetch the correct base URL for firmware downloads.
    - `fw_base_url`: The base URL from which the CMIS CDB firmware binaries can be downloaded. This URL should point to the directory where the firmware binaries are stored. e.g., `http://1.2.3.4/cmis_cdb_firmware/`.

    Example of the file:

    ```csv
    inv_name,fw_base_url
    lab,http://1.2.3.4/cmis_cdb_firmware/
    ```

5. A file (`sonic_{inv_name}_links.csv`) containing the connections of the ports should be present. This file is used to create the topology of the testbed which is required for minigraph generation.

    - `inv_name` - inventory file name that contains the definition of the target DUTs. For further details, please refer to the [Inventory File](https://github.com/sonic-net/sonic-mgmt/blob/master/docs/testbed/README.new.testbed.Configuration.md#inventory-file)

#### 1.1 Link related tests

The following tests aim to validate the link status and stability of transceivers under various conditions.

| Step | Goal | Expected Results |
|------|------|------------------|
| Issue CLI command to shutdown a port | Validate link status using CLI configuration | Ensure that the link goes down |
| Issue CLI command to startup a port | Validate link status using CLI configuration | Ensure that the link is up and the port appears in the LLDP table. |
| In a loop, issue startup/shutdown command 100 times | Stress test for link status validation | Ensure link status toggles to up/down appropriately with each startup/shutdown command. Verify ports appear in the LLDP table when the link is up |
| Restart `xcvrd` | Test link and xcvrd stability | Confirm `xcvrd` restarts successfully without causing link flaps for the corresponding ports, and verify their presence in the LLDP table. Also ensure that xcvrd is up for at least 2 mins |
| Induce I2C errors and restart `xcvrd` | Test link stability in case of `xcvrd` restart + I2C errors | Confirm `xcvrd` restarts successfully without causing link flaps for the corresponding ports, and verify their presence in the LLDP table |
| Modify xcvrd.py to raise an Exception and induce a crash | Test link and xcvrd stability | Confirm `xcvrd` restarts successfully without causing link flaps for the corresponding ports, and verify their presence in the LLDP table. Also ensure that xcvrd is up for at least 2 mins |
| Restart `pmon` | Test link stability | Confirm `xcvrd` restarts successfully without causing link flaps for the corresponding ports, and verify their presence in the LLDP table |
| Restart `swss` | Validate transceiver re-initialization and link status post container restart | Ensure `xcvrd` restarts (for Mellanox platform, ensure pmon restarts) and the expected ports link up again, with port details visible in the LLDP table |
| Restart `syncd` | Validate transceiver re-initialization and link status post container restart | Ensure `xcvrd` restarts (for Mellanox platform, ensure pmon restarts) and the expected ports link up again, with port details visible in the LLDP table |
| Perform a config reload | Test transceiver re-initialization and link status | Ensure `xcvrd` restarts and the expected ports link up again, with port details visible in the LLDP table |
| Execute a cold reboot | Validate transceiver re-initialization and link status post-device reboot | Confirm the expected ports link up again post-reboot, with port details visible in the LLDP table |
| In a loop, execute cold reboot 100 times | Stress test to validate transceiver re-initialization and link status with cold reboot | Confirm the expected ports link up again post-reboot, with port details visible in the LLDP table |
| Execute a warm reboot (if platform supports it) | Test link stability through warm reboot | Ensure `xcvrd` restarts and maintains link stability for the interested ports, with their presence confirmed in the LLDP table |
| Execute a fast reboot (if platform supports it) | Validate transceiver re-initialization and link status post-device reboot | Confirm the expected ports link up again post-reboot, with port details visible in the LLDP table |

#### 1.2 `sfputil` Command Tests

The following tests aim to validate various functionalities of the transceiver (transceiver) using the `sfputil` command.

| Step | Goal | Expected Results |
|------|------|------------------|
| Verify if transceiver presence works with CLI | Transceiver presence validation | Ensure transceiver presence is detected |
| Reset the transceiver followed by issuing shutdown and then startup command | Transceiver reset validation | Ensure that the port is linked down after reset and is in low power mode (if transceiver supports it). Also, ensure that the DataPath is in DPDeactivated state and LowPwrAllowRequestHW (page 0h, byte 26.6) is set to 1. The shutdown and startup commands are later issued to re-initialize the port and bring the link up |
| Put transceiver in low power mode (if transceiver supports it) followed by restoring to high power mode | Transceiver low power mode validation | Ensure transceiver is in high power mode initially. Then put the transceiver in low power mode and ensure that the port is linked down and the DataPath is in DPDeactivated state. Ensure that the port is in low power mode through CLI. Disable low power mode and ensure that the link is up now and transceiver is in high power mode now |
| Verify EEPROM of the transceiver using CLI | Transceiver specific fields validation from EEPROM | Ensure transceiver specific fields are matching with the values retrieved from the transceiver dictionary created using the csv files |
| Verify DOM information of the transceiver using CLI when interface is in shutdown and no shutdown state (if transceiver supports DOM) | Basic DOM validation | Ensure the fields are in line with the expectation based on interface shutdown/no shutdown state |
| Verify EEPROM hexdump of the transceiver using CLI | Transceiver EEPROM hexdump validation | Ensure the output shows Lower Page (0h) and Upper Page (0h) for all 128 bytes on each page. Information from the transceiver dictionary created using the csv files can be used to validate contents of page 0h. Also, ensure that page 11h shows the Data Path state correctly |
| Verify firmware version of the transceiver using CLI (requires disabling DOM config) | Firmware version validation | Ensure the active and inactive firmware version is in line with the expectation from the transceiver dictionary created using the csv files |
| Verify different types of loopback | Transceiver loopback validation | Ensure that the various supported types of loopback work on the transceiver. The LLDP neighbor can also be used to verify the data path after enabling loopback (such as host-side input loopback) |

#### 1.3 `sfpshow` Command Tests

The following tests aim to validate various functionalities of the transceiver using the `sfpshow` command.

| Step | Goal | Expected Results |
|------|------|------------------|
| Verify transceiver specific information through CLI | Validate CLI relying on redis-db | Ensure transceiver specific fields match the values retrieved from transceiver dictionary created using the csv files |
| Verify DOM data is read correctly and is within an acceptable range (if transceiver supports DOM) | Validate CLI relying on redis-db | Ensure DOM data is read correctly and falls within the acceptable range |
| Verify transceiver status when the interface is in shutdown and no shutdown state | Validate CLI relying on redis-db | Ensure the fields align with expectations based on the interface being in shutdown or no shutdown state |
| Verify PM information (for C-CMIS transceivers) | Validate CLI relying on redis-db | Ensure that the PM related fields are populated |
| Verify VDM information for CMIS cables | Validate CLI relying on redis-db | Ensure that all the Pre-FEC and FERC media and host related VDM related fields are populated. The acceptable values for Pre-FEC fields are from 0 through 1e-4 and the FERC values should be <= 0|
| Verify transceiver error-status | Validate CLI relying on redis-db | Ensure the relevant port is in an "OK" state |
| Verify transceiver error-status with hardware verification | Validate CLI relying on transceiver hardware | Ensure the relevant port is in an "OK" state |

#### 1.4 CMIS CDB Firmware Upgrade Testing

##### 1.4.1 CMIS CDB Firmware Binary Management

###### 1.4.1.1 Firmware Binary Naming Guidelines

CMIS CDB firmware binaries must follow strict naming conventions to ensure compatibility across different filesystems and automation tools.

**Filename Requirements:**

1. **Character Restrictions:**
   - **Must not** contain spaces or special characters except hyphens (`-`), dots (`.`), and underscores (`_`)
   - Must be valid filenames for Windows, Linux, and macOS filesystems
   - Avoid reserved characters: `< > : " | ? * \ /`
   - Ensure that the filename does not start or end with special characters

2. **File Extension:**
   - Use `.bin` extension

###### 1.4.1.2 Normalization Rules for Vendor Name and Part Number

To ensure compatibility and uniqueness across filesystems and automation tools, the following normalization rules should be applied to vendor names and part numbers:

> **Important Note:** These normalization rules are designed for test framework consumption and firmware binary storage organization. They are **not** applied to the actual transceiver EEPROM data, which remains unchanged.

**Core Normalization Rules:**

1. **Character Replacement:**
   - Preserve hyphens (`-`) and underscores (`_`) as they are filesystem-safe
   - Replace all other non-alphanumeric characters (spaces, `/`, `.`, `&`, `#`, `@`, `%`, `+`, etc.) with underscores (`_`)
   - Handle consecutive special characters by replacing sequences with a single underscore

2. **Cable Length Normalization:**
   - **Purpose:** Standardize part numbers that differ only by cable length to enable firmware sharing across length variants
   - **Replacement Format:** `GENERIC_N_END<UNIT>` where `N` = number of digits in the original length
   - **Preservation:** Non-unit suffixes after length are preserved (e.g., `10YY` → `GENERIC_2_ENDYY`)

   **Cable Length Examples:**

   | Original Part Number         | Normalized Part Number                  | Explanation |
   |-----------------------------|-----------------------------------------|-------------|
   | QSFP-100G-AOC-15M           | QSFP-100G-AOC-GENERIC_2_ENDM            | 15 has 2 digits, M unit preserved |
   | QSFP-100G-AOC-10YY          | QSFP-100G-AOC-GENERIC_2_ENDYY           | 10 has 2 digits, YY suffix preserved |
   | QSFP-100G-AOC-100           | QSFP-100G-AOC-GENERIC_3_END             | 100 has 3 digits, no unit |
   | QSFP-100G-AOC-3M            | QSFP-100G-AOC-GENERIC_1_ENDM            | 3 has 1 digit, M unit preserved |
   | SFP-1000M                   | SFP-GENERIC_4_ENDM                      | 1000 has 4 digits, M unit preserved |

3. **Cleanup and Formatting:**
   - Remove leading and trailing underscores
   - Replace multiple consecutive underscores with a single underscore
   - Convert the entire result to uppercase for consistency

4. **Usage:**
   - Use normalized names for directory structures and firmware binary organization
   - Enable firmware inventory management across cable length variants
   - Ensure cross-platform filesystem compatibility

**Vendor Name Examples:**

| Original Vendor Name    | Normalized Vendor Name | Explanation |
|------------------------|------------------------|-------------|
| ACME Corp.             | ACME_CORP              | Space and dot replaced with underscore |
| Example & Co           | EXAMPLE_CO             | Ampersand and space replaced |
| Vendor/Inc             | VENDOR_INC             | Slash replaced with underscore |
| Multi___Underscore     | MULTI_UNDERSCORE       | Multiple underscores consolidated |

Sample script to normalize vendor name and part number (script assumes that the length is already replaced with `GENERIC_N_END`):

```python
import re
def normalize_vendor_field(field: str) -> str:
    """
    Normalize vendor name or part number according to the rules:
    - Except for '-' and '_', all non-alphanumeric characters are replaced with '_'
    - Replace any sequence of '_' with a single '_'
    - Remove leading/trailing underscores
    - Convert the result to uppercase
    - Hyphens are preserved
    """
    # Replace all non-alphanumeric except '-' and '_' with '_'
    field = re.sub(r"[^\w\-]", "_", field)
    # Replace multiple consecutive '_' with single '_'
    field = re.sub(r"_+", "_", field)
    # Remove leading/trailing underscores
    field = field.strip("_")
    # Convert to uppercase
    return field.upper()
```

###### 1.4.1.3 Firmware Binary Storage on SONiC Device

The CMIS CDB firmware binaries are stored under `/tmp/cmis_cdb_firmware/` on the SONiC device, organized by normalized vendor name and part number.

**Directory Structure Requirements:**

```
/tmp/cmis_cdb_firmware/
├── <NORMALIZED_VENDOR_NAME>/
│   └── <NORMALIZED_VENDOR_PART_NUMBER>/
│       ├── FIRMWARE_BINARY_1.bin
│       └── FIRMWARE_BINARY_2.bin
└── ...
```

**Requirements:**

- All directory and file names **must be uppercase** and follow the normalization rules defined in section 1.4.1.2
- Use the `GENERIC_N_END` placeholder for cable lengths as described in the normalization rules

**Example Directory Structure:**

```
/tmp/cmis_cdb_firmware/
├── ACMECORP/
│   └── QSFP-100G-AOC-GENERIC_2_ENDM/
│       ├── ACMECORP_QSFP-100G-AOC-GENERIC_2_ENDM_1.2.3.bin
│       └── ACMECORP_QSFP-100G-AOC-GENERIC_2_ENDM_1.2.4.bin
├── EXAMPLE_INC/
│   └── QSFP_200G_LR4/
│       └── EXAMPLE_INC_QSFP_200G_LR4_2.0.1.bin
└── ...
```

###### 1.4.1.4 Firmware Binary Storage on Remote Server

The CMIS CDB firmware binaries must be stored on a remote server with the following requirements:

**Server Organization:**

- Directory structure should mirror the SONiC device structure described above
- Server must be accessible via HTTP/HTTPS protocols
- Base URL configuration is defined in `cmis_cdb_firmware_base_url.csv`

**Base URL Configuration:**
The `cmis_cdb_firmware_base_url.csv` file contains the mapping between inventory files and their corresponding firmware download URLs:

```csv
inv_name,fw_base_url
lab,http://firmware-server.example.com/cmis_cdb_firmware
production,https://secure-firmware.example.com/cmis_cdb_firmware
```

> Note: The `fw_base_url` should not end with a trailing slash (`/`). The test framework will append the necessary path components based on the normalized vendor name and part number.

**Download URL Format:**
Firmware binaries are accessed using the following URL pattern:
```
<fw_base_url>/<NORMALIZED_VENDOR_NAME>/<NORMALIZED_VENDOR_PART_NUMBER>/<FIRMWARE_BINARY_NAME>
```

**Example:**
```
http://firmware-server.example.com/cmis_cdb_firmware/ACMECORP/QSFP-100G-AOC-GENERIC_2_ENDM/ACMECORP_QSFP-100G-AOC-GENERIC_2_ENDM_1.2.4.bin
```

##### 1.4.2 CMIS CDB Firmware Copy to DUT via sonic-mgmt infrastructure

This section describes the automated process for copying firmware binaries to the DUT, ensuring only the required firmware versions are present for testing.

**Firmware Selection Algorithm:**

To ensure only the necessary firmware binaries are present for each transceiver:

1. **Parse `transceiver_firmware_info.csv`** to obtain the list of available firmware binaries, their versions, and associated vendor and part numbers.
2. **Parse `transceiver_dut_info.csv`** to identify the transceivers present on each DUT.
3. **Parse `transceiver_common_attributes.csv`** to get the gold firmware version for each transceiver type.
4. **For each unique combination of normalized vendor name and normalized part number on the DUT**, perform version sorting and selection:
   - Parse firmware versions using semantic versioning (X.Y.Z format)
   - Sort available firmware versions in descending order (most recent first)
   - **Selection criteria:**
     - Always include the gold firmware version (from `transceiver_common_attributes.csv`)
     - Include the two most recent firmware versions in addition to the gold version
     - This ensures at least 2 firmware versions are available for upgrade testing, with the gold version guaranteed to be present as the third firmware binary. If there are fewer than 3 firmware versions available for a transceiver, the entire test will fail.
5. **Copy only the selected firmware binaries** to the target directory structure on the DUT.
6. **Validate firmware binary integrity** using MD5 checksums after copying.

**Cleanup:**

- The firmware binary folder on the DUT (`/tmp/cmis_cdb_firmware/`) will be deleted after the test module run is complete to ensure a clean state for subsequent tests
- Cleanup includes removing both the directory structure and any temporary files created during the process

##### 1.4.3 CMIS CDB Firmware Upgrade Tests

**Prerequisites:**

1. **DOM polling must be disabled** to prevent race conditions between I2C transactions and the CDB mode for modules that cannot support CDB background mode.
2. **Platform-specific processes:** On some platforms, `thermalctld` or similar user processes that perform I2C transactions with the module may need to be stopped during firmware operations.
3. **Firmware requirements:**
   - At least two firmware versions must be available for each transceiver type to enable upgrade testing
   - The gold firmware version (specified in `transceiver_common_attributes.csv`) must be available
   - All firmware versions must support the CDB protocol for proper testing
4. **Module capabilities:** The module must support dual banks for firmware upgrade operations.
5. **Network connectivity:** The DUT must have network access to the firmware server specified in `cmis_cdb_firmware_base_url.csv` for downloading firmware binaries.

| TC No. | Test | Steps | Expected Results |
|------|------|------|------------------|
| 1 | Firmware download validation | 1. Download the gold firmware using the sfputil CLI<br>2. Wait until CLI execution completes | 1. CLI execution should finish within 30 mins and return 0 <br>2. Active FW version should remain unchanged<br>3. Inactive FW version should reflect the gold firmware version<br> 4. No link flap should be seen<br>5. The kernel has no error messages in syslog<br>6. Critical process such as `xcvrd`, `syncd`  `orchagent` does not crash/restart. |
| 2 | Firmware activation validation | 1. Shut down all the interfaces part of the physical ports<br>2. Execute firmware run<br>3. Execute firmware commit<br>4. Reset the transceiver and wait for 5 seconds<br>5. Startup all the interfaces in Step 1 | 1. The return code on step 2 and 3 is 0 (Return code 0 indicates success)<br>2. Active firmware version should now match the previous inactive firmware version<br>3. Inactive firmware version should now match the previous active firmware version<br>4. `sfputil show fwversion` CLI now should show the “Committed Image” to the current active bank<br>5. Critical process such as `xcvrd`, `syncd`  `orchagent` does not crash/restart. |
|3 | Firmware download validation with invalid firmware binary | Download an invalid firmware binary (any file not released by the vendor) | 1. The active firmware version does not change<br>2. The inactive firmware version remains unchanged or is set to `0.0.0` or `N/A`<br> 3.  No change in "Committed Image"<br>4. No link flap should be seen<br>5. The kernel has no error messages in syslog<br>6. Critical process such as `xcvrd`, `syncd`  `orchagent` does not crash/restart. |
|4 | Firmware download abort | 1. Start the firmware download and abort at approximately 10%, 40%, 70%, 90%, and 95%<br>2. Use CTRL+C or kill the download process<br>3. OR reset the optics using sfputil reset<br>4. OR remove the optics and re-insert | 1. Active firmware version remains unchanged<br>2. Inactive firmware version is invalid i.e. N/A or 0.0.0<br>3. No change in "Committed Image"<br>4. Critical process such as `xcvrd`, `syncd`  `orchagent` does not crash/restart. |
|5 | Successful firmware download after aborting | 1. Perform steps in TC #4 followed by TC #1 | All the expectation of test case #4 and case #1 must be met |
|6 | Firmware download validation post reset | 1. Perform steps in TC #1<br>2. Execute `sfputil reset PORT` and wait for it to finish | All the expectation of test case #1 must be met |
|7 | Ensure static fields of EEPROM remain unchanged | 1. Perform steps in TC #1<br>2. Perform steps in TC #2 | 1. All the expectations of TC #1 and #2 must be met<br>2. Ensure after each step 1 and 2 that the static fields of EEPROM (e.g., vendor name, part number, serial number, vendor date code, OUI, and hardware revision) remain unchanged |

#### 1.5 Remote Reseat related tests

The following tests aim to validate the functionality of remote reseating of the transceiver module.
All the below steps should be executed in a sequential manner.

| TC No. | Step | Goal | Expected Results |
|------|------|------|------------------|
|1 | Issue CLI command to disable DOM monitoring | Remote reseat validation | Ensure that the DOM monitoring is disabled for the port |
|2 | Issue CLI command to shutdown the port | Remote reseat validation | Ensure that the port is linked down |
|3 | Reset the transceiver followed by a sleep for 5s | Transceiver reset validation | Ensure reset command executes successfully |
|4 | Put transceiver in low power mode (if LPM supported) | Remote reseat validation | Ensure that the port is in low power mode |
|5 | Put transceiver in high power mode (if LPM supported) | Remote reseat validation | Ensure that the port is in high power mode |
|6 | Issue CLI command to startup the port | Remote reseat validation | Ensure that the port is linked up and is seen in the LLDP table |
|7 | Issue CLI command to enable DOM monitoring for the port | Remote reseat validation | Ensure that the DOM monitoring is enabled for the port |

#### 1.6 Transceiver Specific Capabilities

##### 1.6.1 General Tests

| Step | Goal | Expected Results |
|------|------|------------------|
| Add `"skip_xcvrd": true,` to the `pmon_daemon_control.json` file and reboot the device | Ensure CMIS transceiver is in low power mode upon boot-up | Ensure the transceiver is in low power mode after device reboot. Revert back the file to original after verification |
| Disable the Tx by directly writing to the EEPROM/or by calling `tx_disable` API | Ensure Tx is disabled within the advertised time for CMIS transceivers | Ensure that the DataPath state changes from DPActivated to a different state within the MaxDurationDPTxTurnOff time (page 1h, byte 168.7:4). Issue shut/no shutdown command to restore the link. This can be a stress test |
| Adjust FEC mode | Validate FEC mode adjustment for transceivers supporting FEC | Ensure that the FEC mode can be adjusted to different modes and revert to original FEC mode after testing |
| Validate FEC stats counters | Validate FEC stats counters | Ensure that FEC correctable, uncorrectable and symbol errors have integer values |

##### 1.6.2 C-CMIS specific tests

| Step | Goal | Expected Results |
|------|------|------------------|
| Adjust frequency | Validate frequency adjustment for C-CMIS transceivers | Ensure that the frequency can be adjusted to minimum and maximum supported frequency and revert to original frequency after testing |
| Adjust tx power | Validate tx power adjustment for C-CMIS transceivers | Ensure that the tx power can be adjusted to minimum and maximum supported power and revert to original tx power after testing |

##### 1.6.3 VDM specific tests

**Prerequisites:**

1. DOM polling must be disabled to prevent race conditions between I2C transactions and the CDB mode for modules that cannot support CDB background mode.
2. Python APIs must be available to read the VDM data from the transceiver. The relevant APIs can be found at [sfp_optoe_base.py](https://github.com/sonic-net/sonic-platform-common/blob/cb5564c20ac74694f2391759f9235eee428a97d0/sonic_platform_base/sonic_xcvr/sfp_optoe_base.py#L58-L134)

| TC No. | Test | Steps | Expected Results |
|------|------|------|------------------|
|1 | VDM freeze when all the lanes have Tx enabled | 1. Set `FreezeRequest` = 1<br>2. Sleep for 10ms (`tVDMF` time)<br>3. Wait for `FreezeDone` bit == 1 | 1. Ensure `FreezeDone` is set within 500ms in step 3<br>2. Ensure all the VDM relevant sample groups and flag registers can be read successfully |
|2 | VDM unfreeze when all the lanes have Tx enabled  | 1. Set `FreezeRequest` = 0<br>2. Sleep for 10ms (`tVDMF` time)<br>3. Wait for `UnfreezeDone` bit == 1 | 1. Ensure UnfreezeDone is set within 500ms in step 3 |
|3 | VDM freeze and unfreeze when 1 or more lanes have Tx disabled   | 1. Shutdown the first lane of the physical port<br>2. Repeat the steps of TC #1<br>3. Repeat the steps of TC #2<br>4. Increase the number of lanes shutdown by 1 until all 8 lanes are disabled | 1. For step 2, follow the expectations of TC #1<br>2. For step 3, follow the expectations of TC #2 |
|4| VDM freeze and unfreeze with non sequential lanes Tx disabled | 1. Shutdown all the odd-numbered lanes of the physical port<br>2. Repeat the steps of TC #1<br>3. Repeat the steps of TC #2<br>4. Startup all the odd-numbered lanes and shutdown all the even-numbered lanes of the physical port and repeat step #2 and #3 | 1. For step 2, follow the expectations of TC #1<br>2. For step 3, follow the expectations of TC #2 |

#### CLI commands

**Note**

1. `<port>` in the below commands should be replaced with the logical port number i.e. EthernetXX

2. `<namespace>` in the below commands should be replaced with the asic of the port.

Issuing shutdown command for a port
```
sudo config interface -n '<namespace>' shutdown <port>
```

Issuing startup command for a port
```
sudo config interface -n '<namespace>' startup <port>
```

Check link status of a port
```
show interface status <port>
```

show lldp table
```
show lldp table
```

Enable/disable DOM monitoring for a port

**Note:** For breakout cables, always issue this command for the first subport within the breakout port group, irrespective of the specific subport currently in use.
```
config interface -n '<namespace>' transceiver dom <port> enable/disable

Verification
sonic-db-cli -n '<namespace>' CONFIG_DB hget "PORT|<port>" "dom_polling"

Expected o/p
For enable: "dom_polling" = "enabled" or "(nil)"
For disable: "dom_polling" = "disabled"
```

Restart `xcvrd`

```
docker exec pmon supervisorctl restart xcvrd
```

Get uptime of `xcvrd`

```
docker exec pmon supervisorctl status xcvrd | awk '{print $NF}'
```

Start/Stop `thermalctld` (if applicable)

```
docker exec pmon supervisorctl start thermalctld
OR
docker exec pmon supervisorctl stop thermalctld
```


CLI to get link flap count from redis-db

```
sonic-db-cli -n '<namespace>' APPL_DB hget "PORT_TABLE:<port>" "flap_count"
```

CLI to get link uptime/downtime from redis-db

```
sonic-db-cli -n '<namespace>' APPL_DB hget "PORT_TABLE:<port>" "last_up_time"
sonic-db-cli -n '<namespace>' APPL_DB hget "PORT_TABLE:<port>" "last_down_time"
```

Restart `pmon`

```
sudo systemctl restart pmon
```

Restart `swss`

```
sudo systemctl restart swss
```

Restart `syncd`

```
sudo systemctl restart syncd
```

config reload

```
sudo config reload
```

Cold reboot

```
sudo reboot -f
```

Warm reboot

```
sudo warm-reboot
```

sfputil reset

```
sudo sfputil reset <port>
```

Check if the port is in low power mode

```
sudo sfputil show lpmode -p <port>
```

Put port in low power mode

```
sudo sfputil lpmode on <port>
```

Check lpmode status of a port

```
sudo sfputil show lpmode -p <port>
```

Check if transceiver is present

```
sudo sfputil show presence -p <port>
```

Dump EEPROM of the transceiver

```
sudo sfputil show eeprom -p <port>
```

Dump EEPROM DOM information of the transceiver and verify fields based on the below information

```
sudo sfputil show eeprom -d -p <port>

Verification
For a port in shutdown state, following fields need to be verified
TX<lane_id>Bias is 0mA
TX<lane_id>Power is 0dBm


For a port in no shutdown state, following fields need to be verified
TX<lane_id>Bias is non-zero
TX<lane_id>Power is non-zero

```

Dump EEPROM hexdump of the transceiver

```
sudo sfputil show eeprom-hexdump -p <port> -n <PAGE_NUM>
```

Loopback commands

```
sudo sfputil debug loopback <port> <loopback_type>
```

Check transceiver specific information through CLI relying on redis-db

```
show int transceiver info <port>
```

Check DOM data through CLI relying on redis-db

```
show int transceiver dom <port>
```

Check transceiver status through CLI relying on redis-db and verify fields based on the below information

```
show int transceiver status <port>

Verification
For a port in shutdown state, following fields need to be verified
"TX disable status on lane <lane_id>" is True
"Disabled TX channels" is set for the corresponding lanes
"Data path state indicator on host lane <lane_id>" is DataPathInitialized
"Tx output status on media lane <lane_id>" is False
"Tx loss of signal flag on host lane <lane_id>" is True
"Tx clock and data recovery loss of lock on host lane <lane_id>" is True
"CMIS State (SW):" is READY

For a port in no shutdown state, following fields need to be verified
"TX disable status on lane <lane_id>" is False
"Disabled TX channels" is set to 0 for the corresponding lanes
"Data path state indicator on host lane <lane_id>" is DataPathActivated
"Tx output status on media lane <lane_id>" is True
"Tx loss of signal flag on host lane <lane_id>" is False
"Tx clock and data recovery loss of lock on host lane <lane_id> is False
Verify all the fields containing warning/alarm flags are set to False
"CMIS State (SW):" is READY

```

Check PM information (for C-CMIS transceivers) through CLI relying on redis-db

```
show int transceiver pm <port>
```

Check transceiver error-status through CLI relying on redis-db

```
show int transceiver error-status <port>
```

Check transceiver error-status through CLI relying on transceiver HW

```
show int transceiver error-status -hw <port>
```

Check FW version of the transceiver

```
sudo sfputil show fwversion <port>
```

Download firmware

```
sudo sfputil download <port> <fwfile>
```

Run firmware

```
sudo sfputil firmware run <port>
```

Commit firmware

```
sudo sfputil firmware commit <port>
```

Finding I2C errors from dmesg

```
dmesg -T -L -lerr
```

Get supported min and max frequency from CONFIG_DB

```
sonic-db-cli -n '<namespace>' STATE_DB hget "TRANSCEIVER_INFO|<port>" "supported_max_laser_freq"
sonic-db-cli -n '<namespace>' STATE_DB hget "TRANSCEIVER_INFO|<port>" "supported_min_laser_freq"
```

Adjust frequency

```
config interface -n '<namespace>' transceiver frequency <port> <frequency>
```

Get frequency from CONFIG_DB

```
sonic-db-cli -n '<namespace>' CONFIG_DB hget "PORT|<port>" "laser_freq"
```

Get current laser frequency

```
sonic-db-cli -n '<namespace>' STATE_DB hget "TRANSCEIVER_DOM_SENSOR|<port>" "laser_curr_freq"
```

Get supported min and max tx power from CONFIG_DB

```
sonic-db-cli -n '<namespace>' STATE_DB hget "TRANSCEIVER_INFO|<port>" "supported_max_tx_power"
sonic-db-cli -n '<namespace>' STATE_DB hget "TRANSCEIVER_INFO|<port>" "supported_min_tx_power"
```

Adjust tx power

```
config interface -n '<namespace>'transceiver tx-power <port> <tx_power>
```

Get tx power from CONFIG_DB

```
sonic-db-cli -n '<namespace>' CONFIG_DB hget "PORT|<port>" "tx_power"
```

Get current tx power

```
sonic-db-cli -n '<namespace>' STATE_DB hget "TRANSCEIVER_DOM_SENSOR|<port>" "tx_config_power"
```

Modify pmon_daemon_control.json file to skip xcvrd upon device boot-up

```
platform=$(show version | grep "Platform" | awk -F': ' '{print $2}')
hwsku=$(show version | grep "HwSKU" | awk -F': ' '{print $2}')
cp /usr/share/sonic/device/$platform/$hwsku/pmon_daemon_control.json /usr/share/sonic/device/$platform/$hwsku/pmon_daemon_control.json.orig
#Add "skip_xcvrd": true, to the pmon_daemon_control.json file
```
