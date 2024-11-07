from custom_components.price_tracker.engine.gsthefresh.gsthefresh import GsTheFreshDevice


def createDevice(type: str, attributes: any = None):
    if type == 'gsthefresh':
        return GsTheFreshDevice(device_id=attributes['gs_device_id'], access_token=attributes['access_token'],
                                refresh_token=attributes['refresh_token'], name=attributes['name'],
                                number=attributes['number'], store=attributes['store'])

    return None
