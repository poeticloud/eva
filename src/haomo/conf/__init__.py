import os
import importlib
import logging

from . import global_settings

logger = logging.getLogger(__file__)

ENVIRONMENT_VARIABLE = "HAOMO_SETTINGS_MODULE"
DEFAULT_SETTING_MODULE = "codebase.settings"


class LazySettings:

    _wrapped = None

    def __init__(self):
        self._wrapped = None

    def _setup(self, name=None):
        """
        Load the settings module pointed to by the environment variable. This
        is used the first time we need any settings at all, if the user has not
        previously configured the settings manually.
        """
        try:
            settings_module = os.environ.get(
                ENVIRONMENT_VARIABLE, DEFAULT_SETTING_MODULE
            )
            if not settings_module:  # If it's set but is an empty string.
                raise KeyError
        except KeyError:
            desc = ("setting %s" % name) if name else "settings"
            raise ImproperlyConfigured(
                "Requested %s, but settings are not configured. "
                "You must either define the environment variable %s "
                "or call settings.configure() before accessing settings."
                % (desc, ENVIRONMENT_VARIABLE)
            )

        self._wrapped = Settings(settings_module)

    def __getattr__(self, name):
        # 从环境变量读取
        if name in os.environ:
            return os.environ.get(name)
        # 从配置文件读取
        if self._wrapped is None:
            self._setup(name)
        return getattr(self._wrapped, name)

    def configure(self, default_settings=global_settings, **options):
        """
        Called to manually configure the settings. The 'default_settings'
        parameter sets where to retrieve any unspecified values from (its
        argument must support attribute access (__getattr__)).
        """
        if self._wrapped is not empty:
            raise RuntimeError("Settings already configured.")
        holder = UserSettingsHolder(default_settings)
        for name, value in options.items():
            setattr(holder, name, value)
        self._wrapped = holder

    @property
    def configured(self):
        """
        Returns True if the settings have already been configured.
        """
        return self._wrapped is not empty

    def getbool(self, name):
        v = getattr(self, name)
        if isinstance(v, str):
            return v.lower() not in ["0", "false", "f"]
        return bool(v)

    def getint(self, name):
        v = getattr(self, name)
        if isinstance(v, int):
            return v
        try:
            return int(v)
        except:
            logger.warning(f"settings.{name} is not a int: {v}")
            return 0


class BaseSettings:
    """
    Common logic for settings whether set by a module or by the user.
    """

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)


class Settings(BaseSettings):
    def __init__(self, settings_module):
        # update this dict from global settings (but only for ALL_CAPS settings)
        for setting in dir(global_settings):
            if setting == setting.upper():
                setattr(self, setting, getattr(global_settings, setting))

        # store the settings module in case someone later cares
        self.SETTINGS_MODULE = settings_module

        try:
            mod = importlib.import_module(self.SETTINGS_MODULE)
        except ImportError as e:
            raise ImportError(
                "Could not import settings '%s' (Is it on sys.path? Is there an "
                "import error in the settings file?): %s" % (self.SETTINGS_MODULE, e)
            )

        for setting in dir(mod):
            if setting == setting.upper():
                setting_value = getattr(mod, setting)
                setattr(self, setting, setting_value)

        if not self.SECRET_KEY:
            raise ImproperlyConfigured("The SECRET_KEY setting must not be empty.")


settings = LazySettings()
