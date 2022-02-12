import re
from bs4 import BeautifulSoup
from requests import Session


class DMM:
    session: Session
    host: str = "apidgp-gameplayer.games.dmm.com"
    version: str = "v5"

    mac_address: str
    mac_address: str
    hdd_serial: str
    motherboard: str = "Not Applicable"
    user_os: str = "win"

    def __init__(
        self,
        mac_address: str,
        hdd_serial: str,
        motherboard: str = "Not Applicable",
        user_os: str = "win",
    ) -> None:
        self.session = Session()
        self.session.headers.update(
            {
                "user-agent": "DMMGamePlayer5-Win/5.0.95 Electron/15.1.2",
                "content-type": "application/json",
                "client-app": "DMMGamePlayer5",
                "client-version": "5.0.95",
                "sec-fetch-site": "none",
                "sec-fetch-mode": "no-cors",
                "sec-fetch-dest": "empty",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-US",
            }
        )
        self.mac_address = mac_address
        self.hdd_serial = hdd_serial
        self.motherboard = motherboard
        self.user_os = user_os

    def startup(self):
        """
        {
            "result_code": 100,
            "data": {
                "top_url": "http://app-gameplayer.dmm.com",
                "support_url": "http://app-gameplayer.dmm.com/help",
                "license_url": "https://webdgp-gameplayer.games.dmm.com/v5/gameplayer/agreement?v=2020/08/24",
                "password_forget_url": "https://www.dmm.com/my/-/passwordreminder/",
                "point_url": "https://point.dmm.com/choice/pay?basket_service_type=pcgame",
                "chip_url": "http://www.dmm.com/netgame/lp/-/chip/",
                "agreement_revision_date": "2020/08/24"
            },
            "error": null
        }
        """
        return self.post("/startup")

    def gameplayer_agreement_check(self):
        """
        {
            "result_code": 100,
            "data": {
                "agreement_required": false
            },
            "error": null
        }
        """
        return self.post(
            "/gameplayer/agreement/check",
            {
                "mac_address": self.mac_address,
                "hdd_serial": self.hdd_serial,
                "motherboard": self.motherboard,
                "user_os": self.user_os,
            },
        )

    def login(self, user: str, password: str):
        self.session.headers["content-type"] = "application/x-www-form-urlencoded"
        # fetch login page
        login_url = self.get("loginurl")["data"]["url"]
        login_page = self.session.get(login_url).text
        # setup login args
        login_soup = BeautifulSoup(login_page)
        login_soup_form = login_soup.select_one("section.area-login-mail").select_one(
            "form"
        )
        login_fields = {
            inp.attrs["name"]: inp.attrs["value"]
            for inp in login_soup_form.select("input")
        }
        login_fields["login_id"] = user
        login_fields["password"] = password
        login_fields["save_login_id"] = "0"
        login_fields["use_auto_login"] = "0"
        # execute login
        auth_url = login_soup_form.attrs["action"]
        auth_method = login_soup_form.attrs["method"]
        auth_page_res = self.session.request(auth_method, auth_url, data=login_fields)
        if len(auth_page_res.history) != 1:
            raise ValueError("Login failed")
        # finish authentication
        auth_href = re.search(r'href\s*=\s*"(.+?)"', auth_page_res.text)[1]
        # fix href
        # https\\u003a\\u002f\\u002fwww.dmm.com\\u002fmy\\u002f-\\u002fauthorize\\u002f\\u003fresponse\\u005ftype\\u003dcode\\u0026client\\u005fid\\u003...
        # ->
        # https://www.dmm.com/my/-/authorize/?response_type=code&client_id=....
        #auth_href = re.sub(r"\\u00(\w\w)", lambda x: chr(int(x[1], 16)), auth_href)
        auth_href = eval(f'"{auth_href}"')
        auth1 = self.session.get(auth_href, allow_redirects=False)
        self.session.get(auth1.next.url, allow_redirects=False)
        self.session.headers["content-type"] = "application/json"

    def userinfo(self, type: str = "all"):
        """
        {
            "result_code": 100,
            "data": {
                "point": 0,
                "point_valid": true,
                "chip": 0,
                "chip_valid": true,
                "profile": {
                    "dmm_games_id": "00000000", # <- unique number
                    "nickname": "XYZ",          # <- nick
                    "email": "XYZ@mail.com",    # <- email
                    "avatar_image": "https://webdgp-gameplayer.games.dmm.com/static/image/userProfileDefaultImage.svg"
                },
                "is_profile_registered": true,
                "top_display": "general",
                "open_id": "?",                 # <- short token
                "is_device_authentication_all": false,
                "service_token": "?"            # <- long token
            },
            "error": null
        }
        """
        return self.post("/userinfo", {"type": type})

    def report(self, type: str, product_id: str = "", game_type: str = ""):
        """
        {
            "result_code": 100,
            "data": {
                "result": true
            },
            "error": null
        }
        """

        return self.post(
            "/report", {"type": type, "product_id": product_id, "game_type": game_type}
        )

    def loginrecord(self):
        """
        {
            "result_code": 100,
            "data": null,
            "error": null
        }
        """
        self.report("login")
        return self.post(
            "/loginrecord",
            {
                "mac_address": self.mac_address,
                "hdd_serial": self.hdd_serial,
                "motherboard": self.motherboard,
                "user_os": self.user_os,
            },
        )

    def mygames(self):
        """
        {
            "result_code": 100,
            "data": [{
                "product_id": "ragnador",
                "type": "GCL",
                "is_view": true,
                "total_play_time": 0,
                "is_subsc": false,
                "is_favorite": false,
                "is_game_requires_install": true,
                "expiration_at": null,
                "is_expiration_for_play": false,
                "title": "ラグナドール 妖しき皇帝と終焉の夜叉姫",
                "title_ruby": "らぐなどーるあやしきこうていとしゅうえんのやしゃひめ",
                "package_image_url": "https://pics.dmm.com/digital/gameplayer/ragnador/ragnadorpt.jpg",
                "is_device_authentication": false,
                "is_out_of_print": false,
                "company_name": "株式会社グラムス",
                "target_os_display": ["Windows"]
            }],
            "error": null
        }
        """

        return self.post("/mygames", {"user_os": self.user_os})

    def gameinfo(self, product_id: str, game_type="GCL"):
        """
        {
            "result_code": 100,
            "data": {
                "type": "GCL",
                "product_id": "ragnador",
                "has_detail": true,
                "has_uninstall": true,
                "allow_shortcut_shortcut": false,
                "allow_visible_setting": false,
                "registered_time": null,
                "last_played": null,
                "state": "available",
                "user_state": "none",
                "actions": ["playable"],
                "is_show_latest_version": true,
                "latest_version": "1.0.3.rev12",
                "is_show_file_size": true,
                "file_size": 294171864,
                "is_show_agreement_link": true,
                "update_date": "2021/10/20"
            },
            "error": null
        }        
        """
        return self.post(
            "/gameinfo",
            {
                "product_id": product_id,
                "game_type": game_type,
                "game_os": self.user_os,
                "mac_address": self.mac_address,
                "hdd_serial": self.hdd_serial,
                "motherboard": self.motherboard,
                "user_os": self.user_os,
            },
        )

    def install_cl(self, product_id: str, game_type="GCL"):
        """
        {
            "result_code": 100,
            "data": {
                "product_id": "ragnador",
                "title": "ラグナドール 妖しき皇帝と終焉の夜叉姫",
                "has_installer": false,
                "installer": null,
                "has_modules": false,
                "modules": null,
                "install_dir": "Ragnador",
                "file_list_url": "/gameplayer/filelist/24772",
                "is_administrator": false,
                "file_check_type": "FILELIST",
                "total_size": 294171864,
                "latest_version": "1.0.3.rev12",
                "sdk_type": ""
            },
            "error": null
        }
        """

        return self.post(
            "/install/cl",
            {
                "product_id": product_id,
                "game_type": game_type,
                "game_os": self.user_os,
                "mac_address": self.mac_address,
                "hdd_serial": self.hdd_serial,
                "motherboard": self.motherboard,
                "user_os": self.user_os,
            },
        )

    def launch_cl(self, product_id: str, game_type="GCL", launch_type="LIB"):
        """
        {
            "result_code": 100,
            "data": {
                "product_id": "ragnador",
                "title": "ラグナドール 妖しき皇帝と終焉の夜叉姫",
                "exec_file_name": "Kai.exe",
                "install_dir": "Ragnador",
                "file_list_url": "/gameplayer/filelist/24772",
                "is_administrator": false,
                "file_check_type": "FILELIST",
                "total_size": 294171864,
                "latest_version": "1.0.3.rev12",
                "execute_args": "/viewer_id=000000000 /onetime_token=00000000000000000000000000000000",
                "conversion_url": null,
                "instrumentation_tool": {
                    "is_netcafe": false,
                    "schema_url": "",
                    "game_id": "",
                    "t_stamp": "",
                    "hash": "",
                    "process": ""
                }
            },
            "error": null
        }
        """
        return self.post(
            "/launch/cl",
            {
                "product_id": product_id,
                "game_type": game_type,
                "game_os": self.user_os,
                "launch_type": launch_type,
                "mac_address": self.mac_address,
                "hdd_serial": self.hdd_serial,
                "motherboard": self.motherboard,
                "user_os": self.user_os,
            },
        )

    def filelist_cl(self, product_id: str, game_type="GCL", launch_type="LIB"):
        """
        {
            "result_code": 100,
            "data": {
                "type": "GCL",
                "product_id": "ragnador",
                "title": "ラグナドール 妖しき皇帝と終焉の夜叉姫",
                "latest_version": "1.0.3.rev12",
                "install_dir": "Ragnador",
                "file_list_url": "/gameplayer/filelist/24772",
                "file_check_type": "FILELIST"
            },
            "error": null
        }
        """
        return self.post(
            "/filelist/cl",
            {
                "product_id": product_id,
                "game_type": game_type,
                "game_os": self.user_os,
                "launch_type": launch_type,
                "mac_address": self.mac_address,
                "hdd_serial": self.hdd_serial,
                "motherboard": self.motherboard,
                "user_os": self.user_os,
            },
        )

    def filelist(self, product_id: str, game_type="GCL", launch_type="LIB"):
        """
        {
            "result_code": 100,
            "data": {
                "domain": "https://cdn-gameplayer.games.dmm.com",
                "file_list": [{
                    "local_path": "/DmmAppUninstaller.exe",
                    "path": "product/ragnador/Ragnador/content/win/1.0.3.rev12/data/DmmAppUninstaller.exe",
                    "size": 78603976,
                    "hash": "d2702f8abd8ef8b49959728c397e0b66",
                    "protected_flg": false,
                    "force_delete_flg": false,
                    "check_hash_flg": false,
                    "timestamp": 1634209717000
                }, 
                ....
                }]
            },
            "error": null
        }
        """
        install_info = self.filelist_cl(product_id, game_type, launch_type)["data"]
        return self.session.get(f"https://{self.host}{install_info['file_list_url']}")

    def download_file(self, url: str) -> bytes:
        """
        from filelist
        url = f"{domain}/{file_list[x]['path']}"
        e.g.
        
        "domain": https://cdn-gameplayer.games.dmm.com",
		"file_list": [{
			"local_path": "/DmmAppUninstaller.exe",
			"path": "product/ragnador/Ragnador/content/win/1.0.3.rev12/data/DmmAppUninstaller.exe",
            ...
         }]
        ->
        https://cdn-gameplayer.games.dmm.com/product/ragnador/Ragnador/content/win/1.0.3.rev12/data/DmmAppUninstaller.exe
        """
        res = self.session.post(
            f"https://{self.host}/getCookie", json={"url": url}
        ).json()
        data_res = self.session.get(
            url,
            params={
                "Policy": res.get("policy", ""),
                "Signature": res.get("signature", ""),
                "Key-Pair-Id": res.get("key", ""),
            },
        )
        return data_res.content

    def post(self, path: str, data: str = None) -> dict:
        return self.session.post(
            f"https://{self.host}/{self.version}/{path.strip('/')}", json=data
        ).json()

    def get(self, path: str, data: str = None) -> dict:
        return self.session.get(
            f"https://{self.host}/{self.version}/{path.strip('/')}", json=data
        ).json()
