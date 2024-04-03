from restic_backup_wrapper.log import enable_icecream


def pytest_configure() -> None:
    enable_icecream("[ic] ")
