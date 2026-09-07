from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User
from schemas.user import UserCreate, UserResponse
from utils.dependencies import require_roles
from utils.security import hash_password
from utils.dependencies import require_roles, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


# =========================================================
# ADMIN MANAGEMENT
# =========================================================

# SUPER ADMIN → CREATE ADMIN
@router.post(
    "/admins",
    response_model=UserResponse,
    dependencies=[Depends(require_roles("super_admin"))]
)
def create_admin(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing:
        raise HTTPException(400, "Email already exists")

    new_admin = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
        role="admin"
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return new_admin


# SUPER ADMIN → VIEW ADMINS
@router.get(
    "/admins",
    response_model=list[UserResponse],
    dependencies=[Depends(require_roles("super_admin"))]
)
def get_admins(db: Session = Depends(get_db)):
    return db.query(User).filter(
        User.role == "admin"
    ).all()


# SUPER ADMIN → UPDATE ADMIN
@router.put(
    "/admins/{admin_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_roles("super_admin"))]
)
def update_admin(
    admin_id: int,
    user: UserCreate,
    db: Session = Depends(get_db)
):
    existing_admin = db.query(User).filter(
        User.id == admin_id,
        User.role == "admin"
    ).first()

    if not existing_admin:
        raise HTTPException(404, "Admin not found")

    email_exists = db.query(User).filter(
        User.email == user.email,
        User.id != admin_id
    ).first()

    if email_exists:
        raise HTTPException(400, "Email already exists")

    existing_admin.username = user.username
    existing_admin.email = user.email

    if user.password:
        existing_admin.password_hash = hash_password(
            user.password
        )

    db.commit()
    db.refresh(existing_admin)

    return existing_admin


# SUPER ADMIN → DELETE ADMIN
@router.delete(
    "/admins/{admin_id}",
    dependencies=[Depends(require_roles("super_admin"))]
)
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db)
):
    existing_admin = db.query(User).filter(
        User.id == admin_id,
        User.role == "admin"
    ).first()

    if not existing_admin:
        raise HTTPException(404, "Admin not found")

    db.delete(existing_admin)
    db.commit()

    return {
        "message": "Admin deleted successfully"
    }


# =========================================================
# USER MANAGEMENT
# =========================================================

# ADMIN/SUPER ADMIN → CREATE USER
@router.post(
    "/",
    response_model=UserResponse,
    dependencies=[Depends(require_roles("admin", "super_admin"))]
)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing:
        raise HTTPException(400, "Email already exists")

    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
        role="user"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ADMIN/SUPER ADMIN → VIEW USERS
@router.get(
    "/",
    response_model=list[UserResponse],
    dependencies=[Depends(require_roles("admin", "super_admin"))]
)
def get_users(db: Session = Depends(get_db)):
    return db.query(User).filter(
        User.role == "user"
    ).all()


# ADMIN/SUPER ADMIN → UPDATE USER
@router.put(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_roles("admin", "super_admin"))]
)
def update_user(
    user_id: int,
    user: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.id == user_id,
        User.role == "user"
    ).first()

    if not existing_user:
        raise HTTPException(404, "User not found")

    email_exists = db.query(User).filter(
        User.email == user.email,
        User.id != user_id
    ).first()

    if email_exists:
        raise HTTPException(400, "Email already exists")

    existing_user.username = user.username
    existing_user.email = user.email

    if user.password:
        existing_user.password_hash = hash_password(
            user.password
        )

    db.commit()
    db.refresh(existing_user)

    return existing_user


# ADMIN/SUPER ADMIN → DELETE USER
@router.delete(
    "/{user_id}",
    dependencies=[Depends(require_roles("admin", "super_admin"))]
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.id == user_id,
        User.role == "user"
    ).first()

    if not existing_user:
        raise HTTPException(404, "User not found")

    db.delete(existing_user)
    db.commit()

    return {
        "message": "User deleted successfully"
    }


# ADMIN/SUPER ADMIN → DEACTIVATE USER
@router.patch(
    "/{user_id}/deactivate"
)
def toggle_user_status(
    user_id: int,
    current_user=Depends(
        require_roles("admin", "super_admin")
    ),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Admin cannot deactivate another admin
    if (
        current_user.role == "admin"
        and user.role != "user"
    ):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to change this account"
        )

    # Super admin cannot deactivate themselves
    if (
        current_user.id == user.id
        and current_user.role == "super_admin"
    ):
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate yourself"
        )

    user.is_active = not user.is_active

    db.commit()
    db.refresh(user)

    return {
        "message": (
            "User activated successfully"
            if user.is_active
            else "User deactivated successfully"
        ),
        "user_id": user.id,
        "is_active": user.is_active
    }
    
    
# =========================================================
# PROFILE
# =========================================================

@router.get(
    "/profile",
    response_model=UserResponse
)
def get_profile(
    current_user=Depends(get_current_user)
):
    return current_user


@router.put(
    "/profile",
    response_model=UserResponse
)
def update_profile(
    user: UserCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    email_exists = db.query(User).filter(
        User.email == user.email,
        User.id != current_user.id
    ).first()

    if email_exists:
        raise HTTPException(400, "Email already exists")

    current_user.username = user.username
    current_user.email = user.email

    if user.password:
        current_user.password_hash = hash_password(user.password)

    db.commit()
    db.refresh(current_user)

    return current_user