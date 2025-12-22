from fastapi import APIRouter
from .auth.router import router as auth_router
from .user.router import router as user_router
from .role.router import router as role_router
from .permission.router import router as permission_router
from .quiz.router import router as quiz_router 
from .question.router import router as question_router
from .result.router import router as result_router

router = APIRouter()


router.include_router(auth_router)
router.include_router(user_router)
router.include_router(role_router)
router.include_router(permission_router)

router.include_router(quiz_router)
router.include_router(question_router)
router.include_router(result_router)
