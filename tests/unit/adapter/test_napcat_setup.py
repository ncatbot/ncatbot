"""
NapCat Setup 模块单元测试

覆盖:
  S-01: configure_all() 自动创建 config 目录
  S-02: configure_onebot() 写入正确的 OneBot11 配置
  S-03: configure_onebot() 合并已有配置
  S-04: _install_linux() 不再要求 root 权限
  S-05: LinuxOps.napcat_dir rootless fallback
  S-06: LinuxOps 使用 napcat CLI（不带 sudo/bash）
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ==================== Fixtures ====================


@pytest.fixture
def tmp_napcat_dir(tmp_path):
    """创建临时 napcat 目录结构"""
    napcat_dir = tmp_path / "napcat"
    napcat_dir.mkdir()
    return napcat_dir


@pytest.fixture
def mock_napcat_config():
    """模拟 NapCatConfig"""
    cfg = MagicMock()
    cfg.ws_uri = "ws://127.0.0.1:3001"
    cfg.ws_token = "test_token"
    cfg.ws_listen_ip = "0.0.0.0"
    cfg.enable_webui = False
    cfg.webui_port = 6099
    cfg.webui_token = "webui_token"
    return cfg


@pytest.fixture
def config_manager(tmp_napcat_dir, mock_napcat_config):
    """创建使用临时目录的 NapCatConfigManager"""
    from ncatbot.adapter.napcat.setup.config import NapCatConfigManager

    platform_ops = MagicMock()
    platform_ops.napcat_dir = tmp_napcat_dir
    platform_ops.config_dir = tmp_napcat_dir / "config"

    return NapCatConfigManager(
        platform_ops=platform_ops,
        napcat_config=mock_napcat_config,
        bot_uin="1550507358",
    )


# ==================== S-01: configure_all 自动创建 config 目录 ====================


class TestConfigureAll:
    def test_creates_config_dir_when_missing(self, config_manager, tmp_napcat_dir):
        """S-01: config 目录不存在时 configure_all 自动创建"""
        config_dir = tmp_napcat_dir / "config"
        assert not config_dir.exists()

        config_manager.configure_all()

        assert config_dir.exists()
        assert config_dir.is_dir()

    def test_succeeds_when_config_dir_exists(self, config_manager, tmp_napcat_dir):
        """S-01: config 目录已存在时不报错"""
        config_dir = tmp_napcat_dir / "config"
        config_dir.mkdir()

        config_manager.configure_all()

        assert config_dir.exists()


# ==================== S-02: configure_onebot 写入正确配置 ====================


class TestConfigureOnebot:
    def test_creates_new_config(self, config_manager, tmp_napcat_dir):
        """S-02: 首次运行时生成正确的 OneBot11 配置"""
        config_dir = tmp_napcat_dir / "config"
        config_dir.mkdir()

        config_manager.configure_onebot()

        config_path = config_dir / "onebot11_1550507358.json"
        assert config_path.exists()

        config = json.loads(config_path.read_text(encoding="utf-8"))
        servers = config["network"]["websocketServers"]
        assert len(servers) == 1
        assert servers[0]["port"] == 3001
        assert servers[0]["token"] == "test_token"
        assert servers[0]["host"] == "0.0.0.0"
        assert servers[0]["enable"] is True

    def test_merges_existing_config(self, config_manager, tmp_napcat_dir):
        """S-03: 已有配置时追加 WebSocket 服务器"""
        config_dir = tmp_napcat_dir / "config"
        config_dir.mkdir()

        existing = {
            "network": {"websocketServers": []},
            "musicSignUrl": "https://example.com",
        }
        config_path = config_dir / "onebot11_1550507358.json"
        config_path.write_text(json.dumps(existing), encoding="utf-8")

        config_manager.configure_onebot()

        config = json.loads(config_path.read_text(encoding="utf-8"))
        assert config["musicSignUrl"] == "https://example.com"
        assert len(config["network"]["websocketServers"]) == 1


# ==================== S-04: _install_linux 不再要求 root ====================


class TestInstallLinux:
    @patch("ncatbot.adapter.napcat.setup.installer.subprocess.Popen")
    @patch(
        "ncatbot.adapter.napcat.setup.installer.PlatformOps._confirm_action",
        return_value=True,
    )
    def test_no_root_check(self, mock_confirm, mock_popen):
        """S-04: _install_linux 不调用 _check_root, 不使用 sudo"""
        from ncatbot.adapter.napcat.setup.installer import NapCatInstaller
        from ncatbot.adapter.napcat.setup.platform import LinuxOps

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.wait = MagicMock()
        mock_popen.return_value = mock_process

        platform_ops = MagicMock(spec=LinuxOps)
        installer = NapCatInstaller(platform_ops)

        result = installer._install_linux("install")

        assert result is True
        # 验证调用的命令不包含 sudo
        cmd = mock_popen.call_args[0][0]
        assert "sudo" not in cmd

    @patch("ncatbot.adapter.napcat.setup.installer.subprocess.Popen")
    def test_skip_confirm_skips_prompt(self, mock_popen):
        """S-07: skip_confirm=True 时跳过确认直接安装"""
        from ncatbot.adapter.napcat.setup.installer import NapCatInstaller
        from ncatbot.adapter.napcat.setup.platform import LinuxOps

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.wait = MagicMock()
        mock_popen.return_value = mock_process

        platform_ops = MagicMock(spec=LinuxOps)
        installer = NapCatInstaller(platform_ops)

        result = installer._install_linux("install", skip_confirm=True)

        assert result is True
        mock_popen.assert_called_once()

    @patch("ncatbot.adapter.napcat.setup.installer.subprocess.Popen")
    @patch(
        "ncatbot.adapter.napcat.setup.installer.PlatformOps._confirm_action",
        return_value=False,
    )
    def test_confirm_declined_returns_false(self, mock_confirm, mock_popen):
        """S-07: 用户拒绝确认时返回 False"""
        from ncatbot.adapter.napcat.setup.installer import NapCatInstaller
        from ncatbot.adapter.napcat.setup.platform import LinuxOps

        platform_ops = MagicMock(spec=LinuxOps)
        installer = NapCatInstaller(platform_ops)

        result = installer._install_linux("install")

        assert result is False
        mock_popen.assert_not_called()


# ==================== S-07: install() 公开方法 ====================


class TestInstallerPublicInstall:
    @patch("ncatbot.adapter.napcat.setup.installer.subprocess.Popen")
    def test_install_delegates_with_skip_confirm(self, mock_popen):
        """S-07: install(skip_confirm=True) 传递到 _install_linux"""
        from ncatbot.adapter.napcat.setup.installer import NapCatInstaller
        from ncatbot.adapter.napcat.setup.platform import LinuxOps

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.wait = MagicMock()
        mock_popen.return_value = mock_process

        platform_ops = MagicMock(spec=LinuxOps)
        platform_ops.is_napcat_installed.return_value = False
        installer = NapCatInstaller(platform_ops)

        result = installer.install(skip_confirm=True)

        assert result is True


# ==================== S-05: LinuxOps.napcat_dir rootless fallback ====================


class TestLinuxOpsNapcatDir:
    @patch("ncatbot.adapter.napcat.setup.platform.Path")
    def test_rootless_fallback(self, mock_path_cls):
        """S-05: /opt/QQ 路径不存在时 fallback 到 ~/Napcat/..."""
        from ncatbot.adapter.napcat.setup.platform import LinuxOps

        mock_root_path = MagicMock()
        mock_root_path.exists.return_value = False
        mock_path_cls.return_value = mock_root_path
        mock_path_cls.home.return_value = Path("/home/testuser")

        ops = LinuxOps()
        result = ops.napcat_dir

        result_posix = result.as_posix()
        assert "Napcat" in result_posix
        assert "app_launcher/napcat" in result_posix


# ==================== S-06: LinuxOps 使用 napcat CLI ======================


class TestLinuxOpsNapcatCLI:
    @patch("ncatbot.adapter.napcat.setup.platform.subprocess.Popen")
    def test_is_napcat_running_uses_cli(self, mock_popen):
        """S-06: is_napcat_running 使用 'napcat status'（无 bash/sudo）"""
        from ncatbot.adapter.napcat.setup.platform import LinuxOps

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"PID: 12345"
        mock_process.stdout = mock_stdout
        mock_process.wait = MagicMock()
        mock_popen.return_value = mock_process

        ops = LinuxOps()
        result = ops.is_napcat_running()

        cmd = mock_popen.call_args[0][0]
        assert cmd == ["napcat", "status"]
        assert "sudo" not in cmd
        assert "bash" not in cmd
        assert result is True

    @patch("ncatbot.adapter.napcat.setup.platform.time.sleep")
    @patch("ncatbot.adapter.napcat.setup.platform.subprocess.Popen")
    def test_start_napcat_uses_cli(self, mock_popen, mock_sleep):
        """S-06: start_napcat 使用 'napcat start <uin>'（无 sudo）"""
        from ncatbot.adapter.napcat.setup.platform import LinuxOps

        def make_status_process(output: bytes):
            p = MagicMock()
            p.returncode = 0
            p.stdout = MagicMock()
            p.stdout.read.return_value = output
            p.stderr = MagicMock()
            p.wait = MagicMock()
            return p

        # First call: is_napcat_running(uin) -> not running
        # Second call: is_napcat_running() -> not running
        # Third call: start -> success
        mock_start_process = MagicMock()
        mock_start_process.returncode = 0
        mock_start_process.stdout = MagicMock()
        mock_start_process.wait = MagicMock()

        # Fourth call: is_napcat_running(uin) -> running
        mock_popen.side_effect = [
            make_status_process(b"No running"),
            make_status_process(b"No running"),
            mock_start_process,
            make_status_process(b"PID: 12345, UIN: 123456"),
        ]

        ops = LinuxOps()
        ops.start_napcat("123456")

        # Verify the start call (third Popen call)
        start_call = mock_popen.call_args_list[2]
        cmd = start_call[0][0]
        assert cmd == ["napcat", "start", "123456"]
        assert "sudo" not in cmd

    @patch("ncatbot.adapter.napcat.setup.platform.subprocess.Popen")
    def test_stop_napcat_uses_cli(self, mock_popen):
        """S-06: stop_napcat 使用 'napcat stop'（无 bash/sudo）"""
        from ncatbot.adapter.napcat.setup.platform import LinuxOps

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = MagicMock()
        mock_process.wait = MagicMock()
        mock_popen.return_value = mock_process

        ops = LinuxOps()
        ops.stop_napcat()

        cmd = mock_popen.call_args[0][0]
        assert cmd == ["napcat", "stop"]
        assert "sudo" not in cmd
        assert "bash" not in cmd
