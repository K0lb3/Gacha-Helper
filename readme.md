# Gacha Helper

A collection of scripts to interact with various game stores, primarily gacha ones.

## Requirements
```cmd
pip install requests
pip install bs4
```

## DMM Games
The dmm script targets [DMM Games](ttps://games.dmm.com) and is based on the [DMM GAME PLAYER β](http://www.dmm.com/netgame/top/guide/player_beta_html/=/ch_navi=/).

### startup
```python
# additional dependencies
# pip install getmac
# pip install wmi
from getmac import get_mac_address
import wmi

from dmm import DMM

client = DMM(
    mac_address=get_mac_address().replace(":", ""),
    hdd_serial=",".join(
        item.SerialNumber.strip(" ") for item in wmi.WMI().Win32_PhysicalMedia()
    ),
    motherboard="Not Applicable",
    user_os="win",
)
client.startup()
client.gameplayer_agreement_check()
client.login("username/email", "password")  # same as in client
client.userinfo()
client.loginrecord()
client.mygames()
```

### launch a game
```python
# with client from startup
import os
import subprocess

DMM_GAME_INSTALL_PATH = r"E:\Program Files (x86)\DMM\games"  # paste your path

# request launch arguments
res = client.launch_cl("product_id")["data"]

# build path of the executable
exe_fp = os.path.join(DMM_GAME_INSTALL_PATH, res["install_dir"], res["exec_file_name"])
exec_args = res["execute_args"]

# spawn deteched process
DETACHED_PROCESS = 0x00000008
cmd = [exe_fp, exec_args.split(" ")]
p = subprocess.Popen(
    f"{exe_fp} {exec_args}",
    shell=False,
    stdin=None,
    stdout=None,
    stderr=None,
    close_fds=True,
    creationflags=DETACHED_PROCESS,
)
```

### downloading a game
```python
# with client from startup
import os

DST = r""  # path where the game files should be written to

# get the filelist of the game
res = client.filelist("product_id")["data"]
# open the dmm site of the game and check the url
# usually: https://dg.{product_id}.jp/
# e.g. https://dg.ragnador.jp/ -> product_id == ragnador
# otherwise you can go by name, or simply check the response of client.mygames()
domain = res["domain"]
for file_info in res["filelist"]:
    file_data = client.download_file(url=f"{domain}/{file_info['path']}")
    fp = os.path.join(DST, *file_info["local_path"].strip("/").split("/"))
    with open(fp, "wb") as f:
        f.write(file_data)
```

## QooApp

WIP
