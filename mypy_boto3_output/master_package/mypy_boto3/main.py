import argparse
import importlib
import logging
import pathlib
import shutil
from typing import List, Set

from mypy_boto3.submodules import SUBMODULES, Submodule
from mypy_boto3.version import __version__ as version

ROOT_PATH = pathlib.Path(__file__).absolute().parent
CACHE_PATH = ROOT_PATH / "cache.txt"
BOTO3_STUBS_NAME = "boto3-stubs"
MODULE_NAME = "mypy_boto3"

FUNCTION_TEMPLATE = """{overload}def {name}(
    service_name: {service_name_type},
    region_name: str = None,
    api_version: str = None,
    use_ssl: bool = None,
    verify: Union[str, bool] = None,
    endpoint_url: str = None,
    aws_access_key_id: str = None,
    aws_secret_access_key: str = None,
    aws_session_token: str = None,
    config: Config = None,
) -> {return_type}:
    pass"""

METHOD_TEMPLATE = """    {overload}def {name}(
        self,
        service_name: {service_name_type},
        region_name: str = None,
        api_version: str = None,
        use_ssl: bool = None,
        verify: Union[str, bool] = None,
        endpoint_url: str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        aws_session_token: str = None,
        config: Config = None,
    ) -> {return_type}:
        pass"""


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        MODULE_NAME,
        description=(
            "Service stubs generator for boto3-stubs."
            " Run it after boto3-stubs every update, install or remove services."
            " Use it only with local python installation."
        ),
    )
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("-d", "--debug", action="store_true", help="Hide log output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Verbose log output")
    parser.add_argument("-c", "--clean", action="store_true", help="Remove all generated files")
    return parser


def get_logger(level: int) -> logging.Logger:
    logger = logging.getLogger("mypy_boto3")
    if not logger.handlers:
        formatter = logging.Formatter("%(name)s: %(levelname)-8s %(message)s")
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(level)
        logger.addHandler(stream_handler)
    logger.setLevel(level)
    return logger


def main() -> None:
    parser = get_parser()
    args = parser.parse_args()
    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    if args.quiet:
        log_level = logging.CRITICAL

    logger = get_logger(log_level)
    logger.warning(
        "This tool is no longer required for anntations to work."
        " Remove it: `pip uninstall mypy_boto3`"
    )
    if args.clean:
        file_paths = [
            ROOT_PATH / "cache.txt",
            ROOT_PATH / "boto3_init_gen.py",
            ROOT_PATH / "boto3_session_gen.py",
        ]
        for file_path in file_paths:
            if file_path.exists():
                logger.info("Removing file %s", file_path)
                file_path.unlink()
        (ROOT_PATH / "boto3_init_gen.py").write_text((ROOT_PATH / "boto3_init_stub.py").read_text())
        (ROOT_PATH / "boto3_session_gen.py").write_text(
            (ROOT_PATH / "boto3_session_stub.py").read_text()
        )
        for submodule in SUBMODULES:
            submodule_path = ROOT_PATH / submodule.import_name
            if submodule_path.exists():
                logger.info("Removing folder %s", submodule_path)
                shutil.rmtree(submodule_path)

        package_names = [
            "boto3-stubs",
            "mypy-boto3",
        ]
        for submodule in SUBMODULES:
            if submodule.is_installed:
                package_names.append(submodule.pypi_name)

        logger.info(
            (
                "You can now uninstall boto3-stubs with:\n\n"
                "    python -m pip uninstall %s\n\n"
                "If you want to use auto-typing for boto3.client/resource functions, run:\n\n"
                "    mypy_boto3\n"
            ),
            " ".join(package_names),
        )
        return
    build_package_methods(logger)
    for submodule in SUBMODULES:
        if not submodule.is_installed:
            submodule_path = ROOT_PATH / submodule.import_name
            if submodule_path.exists():
                logger.debug("Removing directory for deleted service %s", submodule_path)
                shutil.rmtree(submodule_path)
            continue
        build_package_stubs(submodule, logger)
    set_cache_key()
    log_install_info(logger)


def set_cache_key() -> None:
    cache_key = ",".join([i.boto3_name for i in SUBMODULES if i.is_active])
    CACHE_PATH.write_text(cache_key)


def add_package_to_index(boto3_name: str) -> None:
    """
    Add new package to index and rebuild it if package is new.
    """
    active_boto3_names: Set[str] = {boto3_name}
    active_submodule = SUBMODULES[0]
    logger = get_logger(logging.INFO)
    if CACHE_PATH.exists():
        active_boto3_names.update(CACHE_PATH.read_text().split(","))

    for submodule in SUBMODULES:
        if submodule.boto3_name in active_boto3_names:
            submodule.is_active = True
        if submodule.boto3_name == boto3_name:
            submodule.is_active = True
            submodule.is_installed = True
            active_submodule = submodule

    logger.info("Active packages: %s", ", ".join([i.boto3_name for i in SUBMODULES if i.is_active]))
    logger.info(
        "Installed packages: %s", ", ".join([i.boto3_name for i in SUBMODULES if i.is_installed])
    )
    build_package_methods(logger)
    build_package_stubs(active_submodule, logger)
    set_cache_key()
    log_install_info(logger)


def _get_proxy_contents(module_name: str) -> str:
    service_module = importlib.import_module(module_name)
    module_all: List[str] = getattr(service_module, "__all__", [])
    all_names = "\n    ".join(['"{}",'.format(i) for i in module_all])
    import_names = "\n    ".join(["{},".format(i) for i in module_all])
    return "from {} import (\n    {}\n)\n\n__all__ = (\n    {}\n)\n".format(
        module_name, import_names, all_names
    )


def build_package_methods(logger: logging.Logger) -> None:
    init_client_functions: List[str] = []
    init_resource_functions: List[str] = []
    session_client_functions: List[str] = []
    session_resource_functions: List[str] = []
    imports: List[str] = []
    active_submodules: List[Submodule] = []
    for submodule in SUBMODULES:
        if not submodule.is_active:
            continue

        active_submodules.append(submodule)
        logger.info(
            "Discovered %s service stubs in %s",
            submodule.class_name,
            submodule.pypi_name,
        )

    for submodule in active_submodules:
        init_client_functions.append(
            FUNCTION_TEMPLATE.format(
                overload="@overload\n" if len(active_submodules) > 1 else "",
                name="client",
                service_name_type='Literal["{}"]'.format(submodule.boto3_name),
                return_type="{}Client".format(submodule.class_name),
            )
        )
        session_client_functions.append(
            METHOD_TEMPLATE.format(
                overload="@overload\n    " if len(active_submodules) > 1 else "",
                name="client",
                service_name_type='Literal["{}"]'.format(submodule.boto3_name),
                return_type="{}Client".format(submodule.class_name),
            )
        )
        imports.append(
            "from mypy_boto3.{} import {}Client".format(
                submodule.import_name,
                submodule.class_name,
            )
        )
        if submodule.has_resource:
            init_resource_functions.append(
                FUNCTION_TEMPLATE.format(
                    overload="@overload\n" if len(active_submodules) > 1 else "",
                    name="resource",
                    service_name_type='Literal["{}"]'.format(submodule.boto3_name),
                    return_type="{}ServiceResource".format(submodule.class_name),
                )
            )
            session_resource_functions.append(
                METHOD_TEMPLATE.format(
                    overload="@overload\n    " if len(active_submodules) > 1 else "",
                    name="resource",
                    service_name_type='Literal["{}"]'.format(submodule.boto3_name),
                    return_type="{}ServiceResource".format(submodule.class_name),
                )
            )
            imports.append(
                "from mypy_boto3.{} import {}ServiceResource".format(
                    submodule.import_name,
                    submodule.class_name,
                )
            )

    if not init_client_functions:
        init_client_functions.append(
            FUNCTION_TEMPLATE.format(
                overload="",
                name="client",
                service_name_type="str",
                return_type="Any",
            )
        )
    if not init_resource_functions:
        init_resource_functions.append(
            FUNCTION_TEMPLATE.format(
                overload="",
                name="resource",
                service_name_type="str",
                return_type="Any",
            )
        )
    if not session_client_functions:
        session_client_functions.append(
            METHOD_TEMPLATE.format(
                overload="",
                name="client",
                service_name_type="str",
                return_type="Any",
            )
        )
    if not session_resource_functions:
        session_resource_functions.append(
            METHOD_TEMPLATE.format(
                overload="",
                name="resource",
                service_name_type="str",
                return_type="Any",
            )
        )

    init_contents: List[str] = [
        "import sys",
        "from typing import overload, Any, Union",
        "from botocore.config import Config",
        "if sys.version_info >= (3, 8):",
        "    from typing import Literal",
        "else:",
        "    from typing_extensions import Literal",
    ]
    init_contents.extend(imports)
    init_contents.append("")
    init_contents.extend(init_client_functions)
    init_contents.extend(init_resource_functions)

    session_contents: List[str] = [
        "import sys",
        "from typing import overload, Any, Union",
        "from botocore.config import Config",
        "if sys.version_info >= (3, 8):",
        "    from typing import Literal",
        "else:",
        "    from typing_extensions import Literal",
    ]
    session_contents.extend(imports)
    session_contents.append("")
    session_contents.append("class Session:")
    session_contents.extend(session_client_functions)
    session_contents.extend(session_resource_functions)

    write_text(ROOT_PATH / "boto3_init_gen.py", "\n".join(init_contents), logger)
    logger.info("Generated annotations for boto3.client and boto3.resource functions")
    write_text(ROOT_PATH / "boto3_session_gen.py", "\n".join(session_contents), logger)
    logger.info(
        "Generated annotations for boto3.Session.client and boto3.Session.resource functions"
    )


def write_text(path: pathlib.Path, text: str, logger: logging.Logger) -> None:
    logger.debug("Updating %s", path)
    path.write_text(text)


def build_package_stubs(submodule: Submodule, logger: logging.Logger) -> None:
    """
    Build index for installed services.
    """
    submodule_path = ROOT_PATH / submodule.import_name

    if not submodule_path.exists():
        logger.debug("Creating directory %s", submodule_path)
        submodule_path.mkdir(exist_ok=True)

    write_text(
        submodule_path / "__init__.py",
        _get_proxy_contents(submodule.module_name),
        logger,
    )
    write_text(
        submodule_path / "client.py",
        _get_proxy_contents("{}.client".format(submodule.module_name)),
        logger,
    )
    logger.info("Generated mypy_boto3.%s.client module" % submodule.import_name)
    write_text(
        submodule_path / "type_defs.py",
        _get_proxy_contents("{}.type_defs".format(submodule.module_name)),
        logger,
    )
    logger.info("Generated mypy_boto3.%s.type_defs module" % submodule.import_name)
    if submodule.has_resource:
        write_text(
            submodule_path / "service_resource.py",
            _get_proxy_contents("{}.service_resource".format(submodule.module_name)),
            logger,
        )
        logger.info("Generated mypy_boto3.%s.service_resource module" % submodule.import_name)
    if submodule.has_waiter:
        write_text(
            submodule_path / "waiter.py",
            _get_proxy_contents("{}.waiter".format(submodule.module_name)),
            logger,
        )
        logger.info("Generated mypy_boto3.%s.waiter module" % submodule.import_name)
    if submodule.has_paginator:
        write_text(
            submodule_path / "paginator.py",
            _get_proxy_contents("{}.paginator".format(submodule.module_name)),
            logger,
        )
        logger.info("Generated mypy_boto3.%s.paginator module" % submodule.import_name)


def log_install_info(logger: logging.Logger) -> None:
    active_submodules: List[Submodule] = [i for i in SUBMODULES if i.is_active]
    if not active_submodules:
        logger.warning(
            "No services submodules discovered, install the ones you use and run this command again"
        )
        logger.info("https://mypy-boto3.readthedocs.io/en/latest/#sub-modules")
        return

    names_str = ""
    for i, submodule in enumerate(active_submodules):
        name = submodule.class_name
        if not i:
            names_str = name
            continue
        if i < len(active_submodules) - 1:
            names_str = "{}, {}".format(names_str, name)
            continue

        names_str = "{} and {}".format(names_str, name)

    logger.info("You can now use %s type annotations.", names_str)
