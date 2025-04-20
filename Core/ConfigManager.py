import json
import os

class ConfigManager:
    def __init__(self, default_config_path, user_config_path):
        self.default_config_path = default_config_path
        self.user_config_path = user_config_path
        self.config = {}
        self.log_level = "balanced"  # Default log level

    def load_config(self):
        """Load the default config and override with user config if available."""
        self.config = self.load_json(self.default_config_path)

        if os.path.exists(self.user_config_path):
            user_config = self.load_json(self.user_config_path)
            self.override_config(user_config)

        self.log_config()  # Log the configuration values based on the log level

        return self.config

    def load_json(self, path):
        """Load a JSON file and return the parsed data."""
        if not os.path.exists(path):
            print(f"Warning: {path} not found.")
            return {}

        with open(path, 'r') as file:
            return json.load(file)

    def override_config(self, user_config):
        """Override default config with user settings."""
        for key, value in user_config.items():
            if key == "log_level":  # Special handling for log_level
                self.log_level = value
            self.config[key] = value

    def log_config(self):
        """Log the configuration values based on the log level."""
        if self.log_level == "minimum" or self.log_level == "balanced":
            print("Configuration loaded.")
        elif self.log_level == "maximum":
            print("Configuration loaded (Detailed):")
            for key, value in self.config.items():
                print(f"{key}: {value}")

    def save_config(self, config, path):
        """Save the current config to a file."""
        with open(path, 'w') as file:
            json.dump(config, file, indent=4)

# Example usage
if __name__ == "__main__":
    default_config_path = "Config/default_config.json"
    user_config_path = "Config/user_config.json"

    config_manager = ConfigManager(default_config_path, user_config_path)
    config = config_manager.load_config()

    print("Loaded Configuration:", config)
