import json
import os

RULE_FILE = "/config/album_rules.json"


class AlbumRules:
    
    _cache = None

    @staticmethod
    def load():

        if AlbumRules._cache is not None:
            return AlbumRules._cache

        if not os.path.exists(RULE_FILE):
            AlbumRules._cache = {}
            return AlbumRules._cache

        with open(
            RULE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            AlbumRules._cache = json.load(f)

        return AlbumRules._cache


    @staticmethod
    def save(rules):
    
        AlbumRules._cache = rules

        os.makedirs(
            os.path.dirname(RULE_FILE),
            exist_ok=True
        )

        with open(
            RULE_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                rules,
                f,
                indent=2,
                ensure_ascii=False
            )


    @staticmethod
    def get(album):

        rules = AlbumRules.load()

        rule = rules.get(album, {})

        defaults = {

            "auto_add": False,

            "allow_delete": False,

            "allow_rename": True

        }

        changed = False

        for key, value in defaults.items():

            if key not in rule:

                rule[key] = value
                changed = True

        if changed:

            rules[album] = rule

            AlbumRules.save(rules)

        return rule

    @staticmethod
    def set(album, **kwargs):
    
        rules = AlbumRules.load()
    
        rule = rules.get(album, {})
    
        defaults = {
            "auto_add": False,
            "allow_delete": False,
            "allow_rename": True,
        }

        defaults.update(rule)
        defaults.update(kwargs)

        rules[album] = defaults

        AlbumRules.save(rules)

        return defaults