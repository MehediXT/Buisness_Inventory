import hashlib
import json

from django.core.cache import cache


PRODUCT_LIST_TTL = 300

def get_product_cache_version(company_id):
    version_key = f"inventory:products:version:{company_id}"

    # Initialize the version if it does not exist.
    cache.add(version_key, 1, timeout=None)

    return cache.get(version_key, 1)


def invalidate_product_list_cache(company_id):
    version_key = f"inventory:products:version:{company_id}"

    # Ensure the version exists before incrementing it.
    cache.add(version_key, 1, timeout=None)
    cache.incr(version_key)


def make_product_list_cache_key(company_id, category, search):
    version = get_product_cache_version(company_id)

    filters = json.dumps(
        {
            "category": category,
            "search": search,
        },
        sort_keys=True,
    )

    filters_hash = hashlib.sha256(
        filters.encode("utf-8")
    ).hexdigest()

    return (
        f"inventory:products:company:{company_id}:"
        f"v{version}:{filters_hash}"
    )
