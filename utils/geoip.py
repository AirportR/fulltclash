import geoip2.database
from geoip2.errors import AddressNotFoundError
from utils.cleaner import config


def geo_info(ip):
    """
    保留原作者信息
    author: https://github.com/Oreomeow
    感谢Oreomeow对于ssrspeedn项目的开源
    部分内容已修改
    """
    country_code, organization, asma = (" ", " ", " ")
    asns = config.config.get("dasn", "GeoLite2-ASN.mmdb")
    citys = config.config.get("dcity", "GeoLite2-City.mmdb")
    orgs = config.config.get("dorg", "GeoLite2-ASN.mmdb")
    try:
        with geoip2.database.Reader(f"resources/databases/{citys}") as reader:
            if "." in ip or ":" in ip:
              country_info = reader.city(ip).country
              country_code = country_info.iso_code
              if country_code == None:
                 country_code = ''
            else:
              country_code = " "

    except AddressNotFoundError as e:
        print(e)

    except ValueError as e:
        print(e)

    try:
        with geoip2.database.Reader(f"resources/databases/{orgs}") as reader:

            if "." in ip or ":" in ip:
              organization = reader.asn(ip).autonomous_system_organization
              if organization == None:
                  organization = ''
            else:
              organization = " "
              

    except AddressNotFoundError as e:
        print(e)
        
    try:
        with geoip2.database.Reader(f"resources/databases/{asns}") as reader:
            if "." in ip or ":" in ip:
              asm = reader.asn(ip).autonomous_system_number
              asma = "AS"+repr(asm)
            else:
              asma = " "
    except AddressNotFoundError as e:
        print(e)
        
    return country_code, organization, asma


if __name__ == "__main__":
    print(geo_info("211.99.101.5"))
