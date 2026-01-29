# TGNPDCL Medical Bill Reimbursement System
## Monolithic Django MVT Application

A complete monolithic Django application with **7 role-based login pages** and **S3 document viewing** across all dashboards.

---

## 🎯 Features

✅ **7 Separate Login Pages** (role-based authentication):
- 🏥 Hospital Admin
- 👤 JPO (Junior Personnel Officer)
- 👥 APO (Assistant Personnel Officer)
- 📋 DPO (Deputy Personnel Officer)
- 💰 FA & CAO (Financial Advisor & Chief Accounts Officer)
- ⚙️ DE (Deputy Engineer)
- 👔 SE / CGM (Senior Engineer / Chief General Manager)

✅ **S3 File Viewing** - All uploaded files visible in dashboards across all 7 roles

✅ **Modern Dark Theme** - Glassmorphism design with role-specific colors

✅ **MVT Architecture** - Pure Django templates (no REST APIs)

✅ **Monolithic Structure** - All services merged into one application

---

## 📁 Project Structure

```
tgnpdcl-monolith/
├── manage.py
├── requirements.txt
├── project/                    # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/                   # Authentication (7 login pages)
│   ├── models.py              # UserProfile with 7 roles
│   ├── views.py               # 7 login views
│   ├── forms.py               # Role-based login form
│   ├── decorators.py          # @role_required
│   └── urls.py
├── hospitals/                  # Hospital management
│   ├── models.py              # Hospital, Bill, LineItem
│   └── views.py
├── workflow/                   # Approval workflow
│   ├── models.py              # WorkflowStep, SanctionRequest
│   └── views.py
├── documents/                  # S3 document storage
│   ├── models.py              # Document (S3)
│   └── views.py
├── static/
│   └── css/
│       └── style.css          # Modern dark theme
└── templates/
    ├── base.html
    ├── accounts/
    │   ├── login_selector.html
    │   └── login.html
    ├── dashboard/
    │   └── dashboard.html     # S3 files visible here
    ├── documents/
    ├── hospitals/
    └── workflow/
```

---

## 🚀 Setup Instructions

### 1. Install System Dependencies

```bash
# Install pip and venv
sudo apt update
sudo apt install python3-pip python3-venv -y
```

### 2. Create Virtual Environment

```bash
cd /home/sam/Desktop/Hospital/tgnpdcl-systems/tgnpdcl-monolith
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (Optional)

For **S3 file storage**, create a `.env` file:

```bash
# AWS S3 Configuration (optional - defaults to local storage)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_S3_REGION_NAME=ap-south-1

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Create Test Users with Roles

```bash
python manage.py shell
```

Then in the Python shell:

```python
from django.contrib.auth.models import User
from accounts.models import UserProfile
from hospitals.models import Hospital

# Create a hospital first
hospital = Hospital.objects.create(
    name="Test Hospital",
    code="TH001",
    tier="TIER1",
    address="123 Test Street"
)

# Create Hospital user
user1 = User.objects.create_user('hospital1', 'hospital@test.com', 'password123')
user1.first_name = 'Hospital'
user1.last_name = 'Admin'
user1.save()
UserProfile.objects.create(user=user1, role='HOSPITAL', hospital=hospital)

# Create JPO user
user2 = User.objects.create_user('jpo1', 'jpo@test.com', 'password123')
user2.first_name = 'JPO'
user2.last_name = 'Officer'
user2.save()
UserProfile.objects.create(user=user2, role='JPO', designation='Junior Personnel Officer')

# Create APO user
user3 = User.objects.create_user('apo1', 'apo@test.com', 'password123')
user3.first_name = 'APO'
user3.last_name = 'Officer'
user3.save()
UserProfile.objects.create(user=user3, role='APO', designation='Assistant Personnel Officer')

# Create DPO user
user4 = User.objects.create_user('dpo1', 'dpo@test.com', 'password123')
user4.first_name = 'DPO'
user4.last_name = 'Officer'
user4.save()
UserProfile.objects.create(user=user4, role='DPO', designation='Deputy Personnel Officer')

# Create FA & CAO user
user5 = User.objects.create_user('facao1', 'facao@test.com', 'password123')
user5.first_name = 'FA'
user5.last_name = 'CAO'
user5.save()
UserProfile.objects.create(user=user5, role='FA_CAO', designation='Financial Advisor & CAO')

# Create DE user
user6 = User.objects.create_user('de1', 'de@test.com', 'password123')
user6.first_name = 'Deputy'
user6.last_name = 'Engineer'
user6.save()
UserProfile.objects.create(user=user6, role='DE', designation='Deputy Engineer')

# Create SE/CGM user
user7 = User.objects.create_user('secgm1', 'secgm@test.com', 'password123')
user7.first_name = 'Senior'
user7.last_name = 'Engineer'
user7.save()
UserProfile.objects.create(user=user7, role='SE_CGM', designation='Senior Engineer / CGM')

print("✅ All 7 test users created!")
exit()
```

### 8. Run Development Server

```bash
python manage.py runserver
```

---

## 🔐 Login Pages

Visit http://localhost:8000 to see the login selector with all 7 options:

| Role | URL | Test Credentials |
|------|-----|------------------|
| Hospital | http://localhost:8000/login/hospital/ | `hospital1` / `password123` |
| JPO | http://localhost:8000/login/jpo/ | `jpo1` / `password123` |
| APO | http://localhost:8000/login/apo/ | `apo1` / `password123` |
| DPO | http://localhost:8000/login/dpo/ | `dpo1` / `password123` |
| FA & CAO | http://localhost:8000/login/fa-cao/ | `facao1` / `password123` |
| DE | http://localhost:8000/login/de/ | `de1` / `password123` |
| SE / CGM | http://localhost:8000/login/se-cgm/ | `secgm1` / `password123` |

---

## 📊 Dashboard Features

After logging in, each role sees:

✅ **Main Dashboard** - Welcome message and recent S3 documents
✅ **Documents Page** - All S3 files with view/download links
✅ **Role-Specific Pages**:
- **Hospital**: Bill management, hospital details
- **Approvers (JPO/APO/DPO/FA&CAO/DE/SE/CGM)**: Approval queue, request processing

---

## 🎨 Design Features

- **Modern Dark Theme** with glassmorphism effects
- **Role-Specific Colors** - Each login page has unique branding
- **Responsive Design** - Works on desktop and mobile
- **Smooth Animations** - Fade-in effects and hover states
- **Google Fonts** - Inter font family for clean typography

---

## 📦 S3 Configuration

The app supports both **local file storage** (default) and **AWS S3**:

- **Without S3**: Files stored in `media/` directory
- **With S3**: Files stored in your S3 bucket

To enable S3, set the environment variables mentioned in step 4.

---

## 🛠️ Admin Panel

Access the Django admin at http://localhost:8000/admin/

Features:
- Manage users and their roles
- View/edit hospitals, bills, documents
- Configure workflow steps
- Set sanction limits

---

## 📝 Notes

- This is a **monolithic application** - all microservices merged into one
- **No REST APIs** - pure Django MVT (Model-View-Template)
- **7 distinct login pages** with role-based access control
- **S3 files visible** in all dashboards
- **Production-ready** with whitenoise for static files

---

## 🔄 Migration from Microservices

This app consolidates:
- `tgnpdcl-hospital-service` → `hospitals` app
- `tgnpdcl-workflow-service` → `workflow` app
- `tgnpdcl-document-service` → `documents` app
- Authentication → `accounts` app

All models, views, and functionality preserved in the monolithic structure.

---

## 📞 Support

For issues or questions, refer to the implementation plan in the `.gemini` directory.
#   T S N P D C L  
 