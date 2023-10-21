from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from sqlalchemy.orm.session import Session
from auth.outh2 import create_access_token

from database.database import get_db
from database.models import User
from database.hashing import verify

router = APIRouter(
    tags=['Authentication']
)


@router.post('/login')
async def login(request: OAuth2PasswordRequestForm = Depends(),
                db: Session = Depends(get_db)):
    request_username = request.username
    user_username = db.query(User).filter(User.username ==
                                          request_username).first()
    user_email = db.query(User).filter(User.email ==
                                       request.username).first()
    
    user = user_email if not user_username else user_username

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Invalid username.')

    if not verify(user.password, request.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Incorrect password.')
    access_token = create_access_token(data={'username': user.username})

    return {
        'access_token': access_token,
        'token_type': 'bearer',
        'user_id': user.id,
        'name': f'{user.first_name} {user.last_name}',
        'username': user.username,
        'user_type': user.user_type,
        'user_image_url': user.user_image_url,
        'created_on': user.created_on
    }
