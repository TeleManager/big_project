from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import PasswordResetForm
from django.conf import settings
from .forms import SignupForm, ProfileUpdateForm, CompanyFileForm, CompanyFileForm2
from django.contrib.auth.views import PasswordChangeView, PasswordResetView, PasswordResetDoneView
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import CompanyFile
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.urls import reverse_lazy, reverse
import os
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders.csv_loader import CSVLoader
from account.forms import PasswordChangeForm
from django.urls import reverse_lazy
import csv
from django.contrib.auth.decorators import login_required
from .forms import ProfileUpdateForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from client.models import Client
from django.contrib.auth.views import LoginView
from .models import Profile

def index(request):
    return render(request, 'registration/login.html')


# 회원가입
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            Profile.objects.create(user=user, is_approved=False)

            return redirect(settings.LOGIN_URL)
    else:
        form = SignupForm()
            
    return render(request, 'registration/signup.html',{'form':form})

@login_required
def profile_update(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('account:profile')  # 프로필 페이지로 리다이렉트
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'registration/profile_update.html', {'form': form})

# 비밀번호 변경
class PasswordChangeView(PasswordChangeView):
    success_url = reverse_lazy('account:login')
    template_name = 'account/password_change_form.html'
    form_class = PasswordChangeForm

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "비밀번호가 성공적으로 변경되었습니다!")
        return super().form_valid(form)


# 비밀번호 찾기
class UserPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset.html'  # 템플릿을 변경하려면 이와 같은 형식으로 입력
    success_url = reverse_lazy('account:password_reset_done')
    form_class = PasswordResetForm

    def form_valid(self, form):
        email = self.request.POST.get("email")
        if User.objects.filter(email=email).exists():
            return super().form_valid(form)
        else:
            return JsonResponse({'email_not_exists': True})

    def form_invalid(self, form):
        response = super().form_invalid(form)
        # 존재하지 않는 이메일인 경우에 대한 처리
        return JsonResponse({'email_not_exists': True})


@login_required
def file_upload(request):
    if request.method == 'POST':
        form = CompanyFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            user_id = request.user.id
            combined_name = f"{user_id}_{uploaded_file.name}"

            # 데이터베이스에서 파일 이름과 사용자 ID로 중복 확인
            if CompanyFile.objects.filter(file=combined_name, user=request.user).exists():
                messages.warning(request, '동일한 파일 이름이 이미 존재합니다.')
                return redirect('client:list')

            fs = FileSystemStorage(location='media/company_data_files/')

            # 파일의 이름이 이미 존재하는지 확인합니다.
            if not fs.exists(combined_name):
                fs.save(combined_name, uploaded_file)
                user_file = form.save(commit=False)
                user_file.user = request.user
                user_file.file = combined_name
                user_file.save()

                ##################################################
                # print(user_file)
                loader = CSVLoader(file_path=f'./media/company_data_files/{combined_name}', encoding='utf-8')
                data = loader.load()

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                texts = text_splitter.split_documents(data)

                # hugging face 임베딩 저장
                model_name = "jhgan/ko-sroberta-multitask"
                model_kwargs = {'device': 'cpu'}
                encode_kwargs = {'normalize_embeddings': False}

                hf = HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs=model_kwargs,
                    encode_kwargs=encode_kwargs
                )
                # 폴더 만들기
                fold_name = combined_name.split(".")[0]
                try:
                    os.makedirs(f'./media/embedding_files/{fold_name}')
                    print("폴더 생성 완료")
                except:
                    print("폴더 존재 or 에러")
                    pass

                # embedding vector 저장
                vectordb_hf = Chroma.from_documents(
                    documents=texts,
                    embedding=hf, persist_directory=f"./media/embedding_files/{fold_name}")
                vectordb_hf.persist()
                ##################################################

                return redirect('client:list')
            else:
                messages.warning(request, '동일한 파일 이름이 이미 존재합니다.')
                return redirect('client:list')
    else:
        form = CompanyFileForm()

    files = CompanyFile.objects.filter(user=request.user)
    return render(request, 'upload/information.html', {'form': form, 'files': files})


# 파일 목록을 출력하는 view입니다.
@login_required
def file_list(request):
    files = CompanyFile.objects.filter(user=request.user)
    return render(request, 'upload/list.html', {'files': files})


@login_required
def edit_file(request, file_id):
    file = get_object_or_404(CompanyFile, id=file_id, user=request.user)

    if request.method == 'POST':
        form = CompanyFileForm2(request.POST, instance=file)
        if form.is_valid():
            form.save()
            return redirect('client:list')  # 클라이언트 목록 뷰로 리디렉션
    else:
        form = CompanyFileForm2(instance=file)

    return render(request, 'upload/edit_file.html', {'form': form, 'file': file})


@login_required
def delete_file(request, file_id):
    file = get_object_or_404(CompanyFile, id=file_id, user=request.user)

    if request.method == 'POST':
        file.delete()
        return redirect('client:list')  # 클라이언트 목록 뷰로 리디렉션

    return render(request, 'upload/delete_file.html', {'file': file})



class DeleteSelectedFilesView(LoginRequiredMixin, View):
    def post(self, request):
        selected_ids = request.POST.getlist('file_ids')  
        #CompanyFile.objects.filter(id__in=selected_ids).delete()  
        
        for s_id in selected_ids:
            CompanyFile.objects.filter()
            file = CompanyFile.objects.get(id=s_id, user=request.user)
            
            
            file_path = os.path.join('media/company_data_files/', file.file.name)
            
            # 파일 삭제
            if os.path.exists(file_path):
                os.remove(file_path)
            
            
            #### 임베딩 폴더 삭제 ####
            
            folder_name = file.file.name.split(".")[0]  # 파일 이름에서 확장자 제거
            folder_path = os.path.join(settings.MEDIA_ROOT, 'embedding_files', folder_name)
        
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                print(f"폴더 {folder_path} 삭제 완료")
            else:
                print(f"폴더 {folder_path}가 이미 없습니다.")
                
            
            ## 모델에서 삭제
            file.delete()    
                
                
        return redirect(reverse('client:list'))  

def before(request):
    return render(request, 'registration/before.html')

class CustomLoginView(LoginView):
    def form_valid(self, form):
        # 기존 로그인 로직을 수행합니다.
        super().form_valid(form)
        
        # 로그인한 사용자를 가져옵니다.
        user = self.request.user
        
        print(user)
        # is_approved 값에 따라 리디렉션합니다.
        profile = Profile.objects.get(user=user)
        if profile and not profile.is_approved:
            logout(self.request)   # logout 시켜줌
            return redirect('account:before')  # before.html로 리디렉션
        else:
            return redirect('index')  # views.index 함수로 리디렉션