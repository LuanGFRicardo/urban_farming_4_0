# Bibliotecas
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from extensions import db
from models import Usuario, DadosColetados, Microcontroladores, Configuracoes
import sqlite3
import requests
import jsonify

# Definir rota de autenticação
bp = Blueprint('auth', __name__, url_prefix='/auth')

# Rota de login
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        nome_usuario = request.form['nome_usuario']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(nome_usuario=nome_usuario).first()
        
        if usuario and usuario.checar_senha(senha):
            login_user(usuario)
            return redirect(url_for('main.home'))
        
        flash('Login inválido. Verifique o nome de usuário e/ou a senha.', 'erro')  
    return render_template('login.html')

# Rota de registro
@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        nome_usuario = request.form['nome_usuario']
        email = request.form['email']
        senha = request.form['senha']
        senha_hash = generate_password_hash(senha)
        usuario = Usuario(nome_usuario=nome_usuario, email=email, senha=senha_hash)
        
        try:
            db.session.add(usuario)
            db.session.commit()
            flash('Sua conta foi criada! Você agora pode fazer login.', 'sucesso')  # Mensagem de sucesso
            return redirect(url_for('auth.login'))
        except:
            db.session.rollback()
            flash('Erro ao criar a conta. Nome de usuário ou e-mail já existe.', 'erro')  # Mensagem de erro
    
    return render_template('register.html')

# Rota de logout
@bp.route('/sair')
@login_required
def sair():
    logout_user()
    return redirect(url_for('auth.confirmacao_logout'))

# Rota de confirmação de logout
@bp.route('/confirmacao_logout')
def confirmacao_logout():
    return render_template('confirmacao_logout.html')

# Rota do perfil
@bp.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html')

# Rota do Dashboard
@bp.route('/dashboard')
@login_required
def dashboard():
    # Obtenha os dados necessários do banco de dados
    dados_temperatura = [20, 21, 22, 23, 24, 25, 24, 23, 22, 21, 20, 19]  # Exemplo de dados de temperatura
    dados_umidade = [60, 62, 65, 64, 63, 60, 62, 61, 60, 59, 58, 57]  # Exemplo de dados de umidade
    dados_pmw = [30, 32, 34, 31, 33, 29, 28, 27, 26, 30, 32, 31]  # Exemplo de dados de PMW
    dados_umidade_solo = [40, 42, 44, 43, 41, 39, 38, 37, 36, 40, 42, 41]  # Exemplo de dados de umidade do solo

    media_temperatura = sum(dados_temperatura) / len(dados_temperatura)
    media_umidade = sum(dados_umidade) / len(dados_umidade)
    media_pmw = sum(dados_pmw) / len(dados_pmw)
    media_umidade_solo = sum(dados_umidade_solo) / len(dados_umidade_solo)
    
    # Definindo uma média de luminosidade com valor padrão
    media_luminosidade = 0  # Substitua pelo cálculo real quando disponível

    return render_template('dashboard-hardcode.html', 
                           media_temperatura=media_temperatura,
                           media_umidade=media_umidade,
                           media_pmw=media_pmw,
                           media_umidade_solo=media_umidade_solo,
                           media_luminosidade=media_luminosidade,
                           data_temperatura=dados_temperatura,
                           data_umidade=dados_umidade,
                           data_pmw=dados_pmw,
                           data_umidade_solo=dados_umidade_solo)

# Rota de Configurações
@bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    microcontroladores = Microcontroladores.query.all()  # Busca todos os microcontroladores
    configuracoes = Configuracoes.query.all()  # Busca todas as configurações

    # Variáveis para armazenar os valores dos LEDs
    luminosidade_leds1 = 0
    luminosidade_leds2 = 0
    luminosidade_leds3 = 0
    
    # Obtenha a configuração atual se o método for GET
    if request.method == 'GET':
        configuracao = Configuracoes.query.first()  # Ou filtre por produto_id, se necessário
        if configuracao:
            luminosidade_leds1 = configuracao.luminosidade_leds1
            luminosidade_leds2 = configuracao.luminosidade_leds2
            luminosidade_leds3 = configuracao.luminosidade_leds3

    if request.method == 'POST':
        microcontrolador_id = request.form['microcontrolador']
        
        if not microcontrolador_id:
            flash('Por favor, selecione um microcontrolador.', 'erro')
            return redirect(url_for('auth.configuracoes'))

        try:
            luminosidade_leds1 = float(request.form.get('luminosidade_leds1', 0))
            luminosidade_leds2 = float(request.form.get('luminosidade_leds2', 0))
            luminosidade_leds3 = float(request.form.get('luminosidade_leds3', 0))
            
            configuracao = Configuracoes.query.filter_by(produto_id=microcontrolador_id).first()
            
            if configuracao:
                configuracao.luminosidade_leds1 = luminosidade_leds1
                configuracao.luminosidade_leds2 = luminosidade_leds2
                configuracao.luminosidade_leds3 = luminosidade_leds3
                db.session.commit()
                flash('Configuração atualizada com sucesso!', 'sucesso')
            else:
                flash('Configuração não encontrada para este microcontrolador!', 'erro')
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro: {str(e)}', 'erro')

    return render_template('configuracoes-hardcode.html', 
                           microcontroladores=microcontroladores, 
                           configuracoes=configuracoes,
                           luminosidade_leds1=luminosidade_leds1,
                           luminosidade_leds2=luminosidade_leds2,
                           luminosidade_leds3=luminosidade_leds3)

@bp.route('/atualizar_leds', methods=['POST'])
@login_required
def atualizar_leds():
    try:
        dados = request.get_json()  # Obter os dados JSON enviados pelo AJAX
        luminosidade_leds1 = dados['luminosidade_leds1']
        luminosidade_leds2 = dados['luminosidade_leds2']
        luminosidade_leds3 = dados['luminosidade_leds3']
        microcontrolador_id = dados['microcontrolador']

        # Aqui você pode fazer a comunicação com o ESP32 via HTTP
        # Exemplo de envio dos dados para o ESP32 (ajuste o IP para o seu dispositivo ESP32)
        esp32_ip = "http://192.168.1.100/update_leds"  # Endereço do ESP32
        response = requests.post(esp32_ip, json={
            "led1": luminosidade_leds1,
            "led2": luminosidade_leds2,
            "led3": luminosidade_leds3
        })

        if response.status_code == 200:
            flash('Configurações enviadas com sucesso!', 'sucesso')
            return jsonify({"success": True}), 200
        else:
            flash('Falha ao enviar configurações ao microcontrolador.', 'erro')
            return jsonify({"success": False}), 500

    except Exception as e:
        flash(f'Ocorreu um erro: {str(e)}', 'erro')
        return jsonify({"success": False}), 500
    
@bp.route('/microcontrolador/<int:microcontrolador_id>', methods=['GET'])
@login_required
def obter_dados_microcontrolador(microcontrolador_id):
    microcontrolador = Microcontroladores.query.get_or_404(microcontrolador_id)
    
    dados = {
        "nome": microcontrolador.nome,
        "descricao": microcontrolador.descricao,
        "empresa": microcontrolador.empresa
    }
    
    return jsonify(dados)