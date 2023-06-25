def get_sale_by_id(id):
    try:
        print(f"ID: {id}")
        api_page = 1
        json_object_day_aux = read_api(API_KEY, id, api_page=api_page, api_name=api_name)
        if (len(json_object_day_aux) < 1):
        elif (len(json_object_day_aux) > 1 and len(json_object_day_aux) < 250):
            total_json += json_object_day_aux
        while (True):
            api_page += 1
            json_object_page_aux = read_api(API_KEY, id, api_page=api_page, api_name=api_name)
            if len(json_object_page_aux) > 1:
                json_object_day_aux += json_object_page_aux
                continue
            elif (len(json_object_page_aux) > 1 and len(json_object_page_aux) < 250):
                json_object_day_aux += json_object_page_aux
                break
            elif (len(json_object_page_aux) < 1):
                break
        total_json += json_object_day_aux
    except Exception as err:
        logging.error(str(err))
        logging.info("Start date: " + str(start_date))
        logging.info("End date: " + str(end_date))
        raise Exception(f"Exception, {str(err)}")
