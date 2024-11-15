from aiogram import Router
# import deleteAllLinks, getLinkFromMessage, getNotionAPI, getUserLinks, userLinks, userLinksChanging
from handlers import deleteAllLinks, getLinkFromMessage, getNotionAPI, getUserLinks, userLinks, userLinksChanging


def setup() -> Router:
    router = Router()

    router.include_routers(deleteAllLinks.r, getLinkFromMessage.r, getNotionAPI.r,
                           getUserLinks.r, userLinks.r, userLinksChanging.r)

    return router
