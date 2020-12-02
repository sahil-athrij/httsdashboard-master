"""This module build a Microsoft Adaptive Card Supported by Webex Teams

https://docs.microsoft.com/en-us/adaptive-cards/getting-started/bots
https://developer.webex.com/docs/api/guides/cards

https://developer.webex.com/buttons-and-cards-designer
https://github.com/CiscoDevNet/webexteamssdk/blob/master/examples/bot-with-card-example-flask.py

The Card is constructed in JSON data structure, the above link to the designer can be used to design and build the JSON representation
of the JSON and assign it to Python nested dictionary variable."""


class Card:
    def __init__(self):
        self.img_url = ""
        self.SR = "SR [{}](http://mwz.cisco.com/{})"
        self.queue = " ({}mins)"
        self.Account = "{}([eportal](https://eportal.cisco.com/#/public/account/{}/gr/overall))"
        self.Tech = ""
        self.SubTech = ""
        self.img_url = "https://drive.google.com/uc?export=view&id="
    
    def CreateCard(self, severity, caseno, queue, InQueueMinutes, AccountName, EportalID, Tech, SubTech, Title, PD, CS, AP):
        if severity == "1":
            img_url = self.img_url + "1Fa_N1LEPiQbHJNpLRQ9DmMbS457ko_kZ"
        elif severity == "2":
            img_url = self.img_url + "1hxXY9hNopRdflKuzOz_nF2uDF-QlGVOK"
        elif severity == "3":
            img_url = self.img_url + "1hBlOOFIeHyhq_NyjfyGeIVsyTnoKb9EY"
        else:
            img_url = self.img_url + "1_bsLkr96GtRDMGp1YesaQm-mg5_TLOyA"
        queue_txt = queue + self.queue.format(InQueueMinutes)
        sr_text = "P{} ".format(severity) + self.SR.format(caseno,caseno)
        customer = self.Account.format(AccountName, EportalID)
        CARD_CONTENT = {
            "type": "AdaptiveCard",
            "body": [
                {
                    "type": "ColumnSet",
                    "columns": [
                        {
                            "type": "Column",
                            "items": [
                                {
                                    "type": "Image",
                                    "style": "Person",
                                    "url": img_url,
                                    "size": "Medium",
                                    "height": "50px"
                                }
                            ],
                            "width": "auto"
                        },
                        {
                            "type": "Column",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": "Cisco HTTS Sydney Bot",
                                    "weight": "Lighter",
                                    "color": "Accent",
                                    "size": "Small"
                                },
                                {
                                    "type": "TextBlock",
                                    "weight": "Bolder",
                                    "text": sr_text,
                                    "horizontalAlignment": "Left",
                                    "wrap": True,
                                    "color": "Light",
                                    "spacing": "Small"
                                }
                            ],
                            "width": "stretch"
                        },
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {
                                    "type": "ActionSet",
                                    "actions": [
                                        {
                                            "type": "Action.Submit",
                                            "title": "Future Usage"
                                        }
                                    ],
                                    "spacing": "Small"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "ColumnSet",
                    "columns": [
                        {
                            "type": "Column",
                            "width": 35,
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": "Queue:",
                                    "color": "Light",
                                    "size": "Small",
                                    "spacing": "Small"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": "Customer:",
                                    "size": "Small",
                                    "spacing": "Small",
                                    "weight": "Lighter",
                                    "color": "Light"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": "Tech:",
                                    "weight": "Lighter",
                                    "color": "Light",
                                    "spacing": "Small",
                                    "size": "Small"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": "Sub-Tech:",
                                    "weight": "Lighter",
                                    "color": "Light",
                                    "spacing": "Small",
                                    "size": "Small"
                                }
                            ]
                        },
                        {
                            "type": "Column",
                            "width": 65,
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": queue_txt,
                                    "color": "Light",
                                    "size": "Small",
                                    "spacing": "Small"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": customer,
                                    "size": "Small",
                                    "spacing": "Small",
                                    "weight": "Lighter",
                                    "color": "Light"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": Tech,
                                    "color": "Light",
                                    "weight": "Lighter",
                                    "spacing": "Small",
                                    "size": "Small"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": SubTech,
                                    "weight": "Lighter",
                                    "color": "Light",
                                    "spacing": "Small",
                                    "wrap": True,
                                    "size": "Small"
                                }
                            ]
                        }
                    ],
                    "spacing": "Padding",
                    "horizontalAlignment": "Center"
                },
                {
                    "type": "TextBlock",
                    "text": Title,
                    "wrap": True
                },
                {
                    "type": "ActionSet",
                    "actions": [
                        {
                            "type": "Action.ShowCard",
                            "title": "Problem Description",
                            "card": {
                                "type": "AdaptiveCard",
                                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                                "fallbackText": "",
                                "body": [
                                    {
                                        "type": "TextBlock",
                                        "text": PD,
                                        "spacing": "Small",
                                        "size": "Small"
                                    }
                                ]
                            }
                        }
                    ],
                    "spacing": "None"
                },
                {
                    "type": "ActionSet",
                    "actions": [
                        {
                            "type": "Action.ShowCard",
                            "title": "Current Status",
                            "card": {
                                "type": "AdaptiveCard",
                                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                                "body": [
                                    {
                                        "type": "TextBlock",
                                        "text": CS,
                                        "spacing": "Small",
                                        "size": "Small"
                                    }
                                ]
                            }
                        }
                    ],
                    "spacing": "None"
                },
                {
                    "type": "ActionSet",
                    "actions": [
                        {
                            "type": "Action.ShowCard",
                            "title": "Action Plan",
                            "card": {
                                "type": "AdaptiveCard",
                                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                                "body": [
                                    {
                                        "type": "TextBlock",
                                        "text": AP,
                                        "size": "Small",
                                        "spacing": "Small"
                                    }
                                ]
                            }
                        }
                    ],
                    "spacing": "None"
                }
            ],
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.2"
        }
        return CARD_CONTENT
