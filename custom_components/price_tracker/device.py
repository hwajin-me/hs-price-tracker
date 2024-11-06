from custom_components.price_tracker.const import DEVICE_ENTITY_ID_FORMAT, DOMAIN, VERSION
from homeassistant.helpers.entity import Entity

class Device(Entity):

    def __init__(self, id: any):
        self._id = id
        self.entity_id = DEVICE_ENTITY_ID_FORMAT.format(id)

    @property
    def unique_id(self):
        return 'device.{}'.format(self.entity_id)

    @property
    def name(self):
        return self._id
    
    @property
    def device_info(self):
        return {
            'connections': {},
            'identifiers': {
                (DOMAIN, self.entity_id)
            },
            'name': self._id,
            'manufacturer': DOMAIN,
            'model': DOMAIN,
            'sw_version': VERSION,
        }
