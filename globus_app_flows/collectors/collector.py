from abc import ABC


class Collector(ABC):
    import_string = None
    # run_authorization_type = "USER"
    # run_authorization_key = None

    def __iter__(self):
        return self

    def __next__(self):
        return self.get_item()

    def __dict__(self):
        raise NotImplemented("Collector does not implement dict")

    def __len__(self):
        raise NotImplemented("Collector does not support item length")

    def get_item(self):
        raise NotImplemented("Collector must implement this method!")

    def get_run_input(self, collection_data, form_data):
        raise NotImplemented("Collector must implement the gut_run_input method!")

    def get_run_start_kwargs(self, collection_data, form_data):
        return {}

    def from_get_request(self, request, *args, **kwargs):
        raise NotImplemented("Collector does not support this")

    def get_metadata(self):
        raise NotImplemented("Collector does not implement this method.")

    # def get_authorization_type(self):
    #     return self.run_authorization_type

    # def get_authorization_key(self):
    #     return self.run_authorization_key

    @classmethod
    def get_import_string(cls):
        if cls.import_string is None:
            raise ValueError("Import String not set on Collector!")
        return cls.import_string
