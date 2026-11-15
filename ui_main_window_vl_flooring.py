# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window_vl_flooring_6.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QCalendarWidget,
    QCheckBox, QComboBox, QDateEdit, QDoubleSpinBox,
    QFormLayout, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QSpinBox,
    QStackedWidget, QTabWidget, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1664, 1041)
        icon = QIcon()
        icon.addFile(u"logo_icon_only_256.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setStyleSheet(u"/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
"   ESTILO GLOBAL \u2014 aplica-se a toda janela e a todo widget que n\u00e3o\n"
"   tenha uma regra mais espec\u00edfica sobrescrevendo depois.\n"
"   \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */\n"
"QMainWindow, QWidget {\n"
"    background-color: #F0F4F8;           /* cor de fundo padr\u00e3o (cinza-azulado cla"
                        "ro) */\n"
"    font-family: \"Segoe UI\", sans-serif;  /* fonte padr\u00e3o de todo o app */\n"
"    font-size: 13px;                      /* tamanho de fonte padr\u00e3o */\n"
"    color: #1C2B3A;                       /* cor de texto padr\u00e3o (azul bem escuro) */\n"
"}\n"
"* { border: none; outline: none; }        /* remove borda/contorno padr\u00e3o de TODOS os widgets (reset) */\n"
"\n"
"/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
"   SIDEBAR (Left_container) \u2014 menu lateral animado\n"
"   \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550"
                        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */\n"
"#Left_container {\n"
"    background-color: #1C2B3A;   /* fundo azul-marinho escuro da sidebar */\n"
"    min-width: 60px;             /* largura m\u00ednima = 60px (estado colapsado) */\n"
"    max-width: 60px;             /* largura m\u00e1xima = 60px (estado colapsado) */\n"
"    margin: 0px 6px 0px 0px;     /* MUDAN\u00c7A: pequena margem s\u00f3 do lado direito, criando um\n"
"                                     \"respiro\" entre a sidebar e o conte\u00fado principal.\n"
"                                     Topo/baixo/esquerda ficam em 0 (colados na borda da janela). */\n"
"    /* IMPORTANTE: min-width e max-width devem ser IGUAIS aqui (60px).\n"
"       O Python (main_.py) controla a anima\u00e7\u00e3o entre 60px <-> 200px\n"
"       via QPropertyAnimation. Se min for maior que max, os dois\n"
"       valores en"
                        "tram em conflito e a sidebar \"briga\" com a anima\u00e7\u00e3o,\n"
"       causando o efeito de layout quebrado/desconfigurado. */\n"
"}\n"
"#Left_container QLabel {\n"
"    color: #FFFFFF;                          /* texto branco (contraste com fundo escuro) */\n"
"    font-size: 15px;\n"
"    font-weight: bold;\n"
"    padding: 14px 8px 10px 8px;              /* respiro em volta do texto (topo direita baixo esquerda) */\n"
"    background-color: #1C2B3A;               /* mesma cor de fundo da sidebar (sem \"quadradinho\" vis\u00edvel) */\n"
"    border-bottom: 1px solid #263849;        /* linha fina separando do conte\u00fado abaixo */\n"
"}\n"
"#Left_container QPushButton {\n"
"    background-color: transparent;   /* bot\u00e3o sem fundo \u2014 s\u00f3 aparece ao passar o mouse ou selecionar */\n"
"    color: #8AAEC8;                  /* azul claro acinzentado \u2014 cor do \u00edcone/texto em repouso */\n"
"    text-align: left;                /* alinha texto/\u00edcone \u00e0 esquerda (n\u00e3o centraliz"
                        "ado) */\n"
"    padding: 10px 0px;               /* respiro vertical entre bot\u00f5es */\n"
"    font-size: 13px;\n"
"    font-weight: 500;\n"
"    border: none;                    /* MUDAN\u00c7A: removida toda borda (antes tinha border-left reservado) */\n"
"    border-radius: 0px;              /* sem cantos arredondados em repouso */\n"
"    margin: 1px 0px;                 /* espa\u00e7amento m\u00ednimo entre um bot\u00e3o e outro */\n"
"}\n"
"#Left_container QPushButton:hover {\n"
"    background-color: #263849;             /* fundo escurece um pouco ao passar o mouse */\n"
"    color: #FFFFFF;                        /* texto/\u00edcone fica branco (mais vis\u00edvel) */\n"
"    border: none;                          /* MUDAN\u00c7A: sem borda no hover tamb\u00e9m */\n"
"}\n"
"#Left_container QPushButton:checked {\n"
"    background-color: #F0F4F8;             /* MUDAN\u00c7A: agora usa a MESMA cor do QStackedWidget (Pages),\n"
"                                                fazendo o bot\u00e3o \"se f"
                        "undir\" visualmente com o conte\u00fado,\n"
"                                                como se fosse uma aba grudada no painel principal */\n"
"    color: #1C2B3A;                        /* MUDAN\u00c7A: texto escuro, j\u00e1 que o fundo agora \u00e9 claro */\n"
"    border: none;                          /* MUDAN\u00c7A: sem borda \u2014 quem indica sele\u00e7\u00e3o agora \u00e9 a cor + o raio */\n"
"    border-top-left-radius: 8px;           /* MUDAN\u00c7A: arredonda s\u00f3 o canto de CIMA \u00e0 esquerda */\n"
"    border-bottom-left-radius: 8px;        /* MUDAN\u00c7A: arredonda s\u00f3 o canto de BAIXO \u00e0 esquerda */\n"
"    font-weight: 600;                      /* texto um pouco mais grosso quando selecionado */\n"
"}\n"
"\n"
"/* Submenu de Registrations (Companies / Contractors / Work Types) dentro da sidebar */\n"
"#frame_registrations_submenu QPushButton {\n"
"    text-align: left;\n"
"    padding-left: 8px;\n"
"    font-size: 16px;\n"
"    background-color: rgba(255,255,255,0.03);  /* b"
                        "ranco quase transparente \u2014 leve destaque do fundo escuro */\n"
"    border: none;\n"
"    border-radius: 4px;\n"
"}\n"
"#frame_registrations_submenu QPushButton:hover {\n"
"    background-color: rgba(255,255,255,0.08);  /* um pouco mais vis\u00edvel ao passar o mouse */\n"
"}\n"
"#frame_registrations_submenu QPushButton:checked {\n"
"    background-color: rgba(255,255,255,0.15);  /* ainda mais vis\u00edvel quando selecionado */\n"
"}\n"
"\n"
"/* Bot\u00e3o de abrir/fechar a sidebar (\u2630) */\n"
"#btn_toggle { padding: 8px 0px; color: #8AAEC8; }\n"
"#btn_toggle:hover { color: #FFFFFF; background-color: #263849; }\n"
"\n"
"/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
"   \u00c1"
                        "REA PRINCIPAL (Main_container) \u2014 tudo \u00e0 direita da sidebar\n"
"   \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */\n"
"#Main_container { background-color: #F0F4F8; }  /* mesmo cinza-claro do fundo geral */\n"
"\n"
"/* Barra superior com o t\u00edtulo da p\u00e1gina + selo do usu\u00e1rio logado */\n"
"#Top_frame {\n"
"    background-color: #FFFFFF;             /* fundo branco, destacando do resto cinza */\n"
"    border-bottom: 1px solid #DDE4EE;      /* linha fina separando do conte\u00fado abaixo */\n"
"    min-height: 50px;                      /* altura fixa m\u00ednima */\n"
"    max-height: 50px;                      /* altura fixa m\u00e1xima (min = max => altura travada e"
                        "m 50px) */\n"
"}\n"
"#Top_frame QLabel {\n"
"    color: #1C2B3A;\n"
"    font-size: 16px;\n"
"    font-weight: 600;\n"
"    padding: 0px 8px;\n"
"    background-color: transparent;\n"
"}\n"
"#lbl_user {\n"
"    color: #FFFFFF;\n"
"    background-color: #1565C0;      /* p\u00edlula azul com o nome/status do usu\u00e1rio */\n"
"    font-size: 12px;\n"
"    font-weight: 600;\n"
"    padding: 4px 12px;\n"
"    border-radius: 20px;            /* raio grande = formato de \"p\u00edlula\" arredondada */\n"
"}\n"
"\n"
"/* Fundo da \u00e1rea onde as p\u00e1ginas (Home, Jobs, Companies...) trocam entre si */\n"
"QStackedWidget { background-color: #F0F4F8; }\n"
"\n"
"/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550"
                        "\u2550\u2550\n"
"   ABAS (QTabWidget) \u2014 usado em Jobs, Companies, Contractors, etc.\n"
"   \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */\n"
"QTabWidget::pane { border: none; background-color: #F0F4F8; }  /* \u00e1rea de conte\u00fado abaixo das abas */\n"
"QTabBar { background-color: #FFFFFF; border-bottom: 1px solid #DDE4EE; }  /* faixa onde ficam as abas */\n"
"QTabBar::tab {\n"
"    background-color: transparent;\n"
"    color: #6B7C93;                          /* cinza \u2014 aba n\u00e3o selecionada */\n"
"    padding: 12px 20px;\n"
"    font-size: 13px;\n"
"    font-weight: 500;\n"
"    border-bottom: 2px solid transparent;    /* reserva espa\u00e7o pra barrinha de \"aba ativ"
                        "a\" */\n"
"    border-radius: 0px;\n"
"}\n"
"QTabBar::tab:hover { color: #1C2B3A; background-color: #F5F8FC; }  /* escurece o texto ao passar o mouse */\n"
"QTabBar::tab:selected {\n"
"    color: #1565C0;                          /* azul \u2014 aba selecionada */\n"
"    border-bottom: 2px solid #1E88E5;        /* barrinha azul embaixo da aba ativa */\n"
"    font-weight: 600;\n"
"    background-color: #FFFFFF;\n"
"}\n"
"\n"
"/* MUDAN\u00c7A: scroll_job_form (a \u00e1rea rol\u00e1vel do formul\u00e1rio de Job) usa a MESMA\n"
"   cor de fundo do QTabWidget::pane acima (#F0F4F8), pra n\u00e3o destacar como um\n"
"   ret\u00e2ngulo diferente por tr\u00e1s dos cart\u00f5es. O seletor \"> QWidget\" pega s\u00f3 o\n"
"   viewport interno do scroll (n\u00e3o afeta os cart\u00f5es brancos l\u00e1 dentro). */\n"
"#scroll_job_form, #scroll_job_form > QWidget {\n"
"    background-color: #F0F4F8;\n"
"    border: none;\n"
"}\n"
"\n"
"/* MUDAN\u00c7A: garante que o FUNDO da aba \"New/Edit Job\" (por tr\u00e1s de todos os\n"
""
                        "   cart\u00f5es) fica explicitamente nessa cor cinza-azulada \u2014 assim os cart\u00f5es\n"
"   brancos (Job Info, Work Types, Client Info, Extra) \"flutuam\" visualmente\n"
"   por cima, em vez de se misturarem com o fundo. */\n"
"#tab_job_form {\n"
"    background-color: #F0F4F8;\n"
"}\n"
"\n"
"/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
"   CART\u00d5ES (QFrame) \u2014 todo cart\u00e3o branco arredondado da interface\n"
"   \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550"
                        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */\n"
"QFrame { background-color: #FFFFFF; border-radius: 8px; }  /* fundo branco + cantos arredondados por padr\u00e3o */\n"
"\n"
"/* Labels de campo (ex: \"WORK DATE\", \"CONTRACTOR\") \u2014 texto pequeno em mai\u00fasculo */\n"
"QLabel { color: #6B7C93; font-size: 11px; font-weight: 600; background-color: transparent; }\n"
"\n"
"/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
"   CAMPOS DE ENTRADA (inputs)\n"
"   \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550"
                        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */\n"
"QLineEdit {\n"
"    background-color: #F5F8FC;       /* fundo cinza bem clarinho */\n"
"    color: #1C2B3A;\n"
"    border: 1px solid #CBD5E1;       /* borda cinza sutil */\n"
"    border-radius: 6px;\n"
"    padding: 8px 12px;\n"
"    font-size: 13px;\n"
"}\n"
"QLineEdit:focus { border: 1px solid #1E88E5; background-color: #FFFFFF; }  /* destaca em azul quando o usu\u00e1rio clica no campo */\n"
"QLineEdit:disabled { background-color: #EEF2F7; color: #9BADBF; }         /* campo \"cinza apagado\" quando desabilitado */\n"
"\n"
"QComboBox {\n"
"    background-color: #F5F8FC;\n"
"    color: #1C2B3A;\n"
"    border: 1px solid #CBD5E1;\n"
"    border-radius: 6px;\n"
"    padding: 7px 12px;\n"
"    font-size: 13px;\n"
"    min-height: 30px;                /* garante altura m\u00ednima consistente com "
                        "os outros campos */\n"
"}\n"
"QComboBox:focus { border: 1px solid #1E88E5; background-color: #FFFFFF; }\n"
"QComboBox::drop-down { border: none; width: 22px; }   /* \u00e1rea clic\u00e1vel da setinha do combo */\n"
"QComboBox QAbstractItemView {\n"
"    background-color: #FFFFFF;                      /* fundo da lista suspensa (dropdown) */\n"
"    border: 1px solid #CBD5E1;\n"
"    border-radius: 6px;\n"
"    selection-background-color: #E3F2FD;            /* item destacado ao passar o mouse/selecionar */\n"
"    selection-color: #1565C0;\n"
"}\n"
"\n"
"QTextEdit {\n"
"    background-color: #F5F8FC;\n"
"    color: #1C2B3A;\n"
"    border: 1px solid #CBD5E1;\n"
"    border-radius: 6px;\n"
"    padding: 8px 12px;\n"
"    font-size: 13px;\n"
"}\n"
"QTextEdit:focus { border: 1px solid #1E88E5; background-color: #FFFFFF; }\n"
"\n"
"/* Campos num\u00e9ricos (valor, quantidade) */\n"
"QDoubleSpinBox, QSpinBox {\n"
"    background-color: #F5F8FC;\n"
"    color: #1C2B3A;\n"
"    border: 1px solid #CBD5E1;\n"
"    bord"
                        "er-radius: 6px;\n"
"    padding: 8px 12px;\n"
"    font-size: 13px;\n"
"}\n"
"QDoubleSpinBox:focus, QSpinBox:focus { border: 1px solid #1E88E5; background-color: #FFFFFF; }\n"
"QDoubleSpinBox:disabled, QSpinBox:disabled { background-color: #EEF2F7; color: #9BADBF; }\n"
"QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,\n"
"QSpinBox::up-button, QSpinBox::down-button {\n"
"    width: 16px;                     /* largura das setinhas de incrementar/decrementar */\n"
"    border: none;\n"
"    background-color: transparent;\n"
"}\n"
"QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover,\n"
"QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #E3F2FD; }  /* destaca a setinha no hover */\n"
"\n"
"/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550"
                        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
"   TABELAS (QTableWidget) \u2014 Job Records, Companies, Contractors...\n"
"   \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */\n"
"QTableWidget {\n"
"    background-color: #FFFFFF;\n"
"    border: 1px solid #DDE4EE;\n"
"    border-radius: 6px;\n"
"    gridline-color: #EEF2F7;                     /* cor das linhas divis\u00f3rias entre c\u00e9lulas */\n"
"    selection-background-color: #E3F2FD;         /* cor de fundo da linha selecionada */\n"
"    selection-color: #1C2B3A;\n"
"    font-size: 13px;\n"
"}\n"
"QTableWidget::item { padding: 8px 10px; border-bottom: 1px solid #EEF2F7; }  /* respiro"
                        " + linha fina entre linhas da tabela */\n"
"QTableWidget::item:selected { background-color: #E3F2FD; color: #1565C0; }  /* cor quando o usu\u00e1rio clica numa linha */\n"
"QHeaderView::section {\n"
"    background-color: #F5F8FC;       /* fundo do cabe\u00e7alho das colunas */\n"
"    color: #6B7C93;\n"
"    font-size: 11px;\n"
"    font-weight: 700;\n"
"    padding: 10px;\n"
"    border: none;\n"
"    border-bottom: 2px solid #DDE4EE;    /* linha grossa separando cabe\u00e7alho do corpo da tabela */\n"
"    border-right: 1px solid #EEF2F7;     /* linha fina separando uma coluna da outra */\n"
"}\n"
"\n"
"/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
"   BOT\u00d5ES (QPushButton) \u2014"
                        " estilo padr\u00e3o + varia\u00e7\u00f5es por objectName\n"
"   \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */\n"
"QPushButton {\n"
"    background-color: #F5F8FC;       /* bot\u00e3o padr\u00e3o: cinza clarinho (ex: \"Refresh\" gen\u00e9rico, \"Cancel\") */\n"
"    color: #1C2B3A;\n"
"    border: 1px solid #CBD5E1;\n"
"    border-radius: 6px;\n"
"    padding: 8px 16px;\n"
"    font-size: 13px;\n"
"    font-weight: 500;\n"
"}\n"
"QPushButton:hover { background-color: #E3F2FD; border-color: #1E88E5; color: #1565C0; }  /* fica azulado ao passar o mouse */\n"
"QPushButton:pressed { background-color: #BBDEFB; }                                        /* mais escuro enquanto pressionado */\n"
""
                        "\n"
"/* Bot\u00f5es \"+ New ...\" \u2014 a\u00e7\u00e3o prim\u00e1ria, sempre azul forte */\n"
"#btn_new_job, #btn_user_create_user, #btn_new_company, #btn_new_contractor, #btn_new_user, #btn_update_user, #btn_new_work_type, #btn_new_expense, #btn_new_product {\n"
"    background-color: #1565C0;\n"
"    color: #FFFFFF;\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    padding: 9px 20px;\n"
"    font-size: 13px;\n"
"    font-weight: 700;\n"
"}\n"
"#btn_new_job:hover, #btn_user_create_user:hover, #btn_new_company:hover, #btn_new_contractor:hover, #btn_new_user:hover, #btn_update_user:hover, #btn_new_product:hover { background-color: #1E88E5; }   /* azul mais claro no hover */\n"
"#btn_new_job:pressed, #btn_user_create_user:pressed, #btn_new_company:pressed, #btn_new_contractor:pressed, #btn_new_user:pressed, #btn_update_user:pressed, #btn_new_product:pressed { background-color: #0D47A1; }  /* azul mais escuro pressionado */\n"
"\n"
"/* Bot\u00f5es \"Save\" \u2014 mesmo azul forte dos bot\u00f5es \"New\" "
                        "(a\u00e7\u00e3o de confirmar) */\n"
"#btn_save_job, #btn_save_company, #btn_save_contractor, #btn_save_user, #btn_save_work_type, #btn_save_expense, #btn_save_product {\n"
"    background-color: #1565C0;\n"
"    color: #FFFFFF;\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    font-size: 13px;\n"
"    font-weight: 700;\n"
"}\n"
"#btn_save_job:hover, #btn_save_company:hover, #btn_save_contractor:hover, #btn_save_user:hover, #btn_save_product:hover { background-color: #1E88E5; }\n"
"\n"
"/* Bot\u00f5es \"Delete\" \u2014 vermelho, indicando a\u00e7\u00e3o destrutiva */\n"
"#btn_delete_job, #btn_delete_company, #btn_delete_contractor, #btn_delete_user, #btn_delete_work_type, #btn_delete_expense, #btn_delete_product {\n"
"    background-color: #C62828;\n"
"    color: #FFFFFF;\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    font-size: 13px;\n"
"    font-weight: 700;\n"
"}\n"
"#btn_delete_job:hover, #btn_delete_company:hover, #btn_delete_contractor:hover, #btn_delete_user:hover, #btn_delete_product:"
                        "hover { background-color: #E53935; }  /* vermelho mais claro no hover */\n"
"\n"
"/* Bot\u00f5es \"Refresh\" \u2014 cinza-azulado escuro, a\u00e7\u00e3o secund\u00e1ria/neutra */\n"
"#btn_refresh_jobs, #btn_refresh_companies, #btn_refresh_contractors, #btn_refresh_users, #btn_refresh_work_types, #btn_refresh_expenses, #btn_refresh_products {\n"
"    background-color: #37474F;\n"
"    color: #FFFFFF;\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    font-size: 13px;\n"
"    font-weight: 600;\n"
"}\n"
"#btn_refresh_jobs:hover, #btn_refresh_companies:hover, #btn_refresh_contractors:hover, #btn_refresh_users:hover, #btn_refresh_products:hover { background-color: #546E7A; }\n"
"\n"
"/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550"
                        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
"   CABE\u00c7ALHOS DE CART\u00c3O (a faixa azul no topo de cada cart\u00e3o,\n"
"   com o t\u00edtulo tipo \"Job Info\", \"Client Info\", \"Work Types\"...)\n"
"   \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */\n"
"#card_header_jobs, #card_header_company, #card_header_contractor, #card_header_user, #card_header_work_type, #card_header_job_info, #card_header_client_info, #card_header_work_types, #card_header_materials, #card_header_expense {\n"
"    background-color: #FFFFFF;             /* MUDAN\u00c7A: fundo branco, igual ao resto do cart\u00e3o (sem faixa colorida) */\n"
"    border-radius: 0px;\n"
"    border-top-left-radius: 8px;        "
                        "   /* arredonda s\u00f3 os cantos de CIMA (mant\u00e9m o mesmo raio do cart\u00e3o) */\n"
"    border-top-right-radius: 8px;\n"
"    max-height: 56px;                      /* altura fixa da faixa */\n"
"    min-height: 56px;\n"
"}\n"
"#card_header_jobs QLabel, #card_header_company QLabel, #card_header_contractor QLabel, #card_header_user QLabel, #card_header_job_info QLabel, #card_header_client_info QLabel, #card_header_work_types QLabel, #card_header_materials QLabel, #card_header_expense QLabel {\n"
"    color: #1C2B3A;               /* MUDAN\u00c7A: texto azul-marinho escuro (j\u00e1 que o fundo agora \u00e9 branco) */\n"
"    font-size: 15px;\n"
"    font-weight: 700;\n"
"    background-color: transparent;\n"
"}\n"
"\n"
"/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550"
                        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
"   BARRAS DE ROLAGEM (scrollbars)\n"
"   \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */\n"
"QScrollBar:vertical { background: #F0F4F8; width: 8px; border-radius: 4px; }\n"
"QScrollBar::handle:vertical { background: #CBD5E1; border-radius: 4px; min-height: 30px; }  /* \"pegador\" da barra */\n"
"QScrollBar::handle:vertical:hover { background: #90A4AE; }                                  /* escurece no hover */\n"
"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }               /* remove as setinhas de cima/baixo */\n"
"QScrollBar:horizontal { background: #F0F4F8; height: 8px"
                        "; border-radius: 4px; }\n"
"QScrollBar::handle:horizontal { background: #CBD5E1; border-radius: 4px; min-width: 30px; }\n"
"QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }            /* remove as setinhas de esquerda/direita */\n"
"\n"
"/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
"   BARRA DE STATUS (rodap\u00e9 da janela) + campo de data\n"
"   \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550"
                        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */\n"
"QStatusBar { background-color: #1C2B3A; color: #8AAEC8; font-size: 12px; padding: 2px 10px; }\n"
"QDateEdit {\n"
"    background-color: #F5F8FC;\n"
"    color: #1C2B3A;\n"
"    border: 1px solid #CBD5E1;\n"
"    border-radius: 6px;\n"
"    padding: 7px 12px;\n"
"    font-size: 13px;\n"
"}\n"
"QDateEdit:focus { border: 1px solid #1E88E5; background-color: #FFFFFF; }\n"
"\n"
"\n"
"\n"
"\n"
"QScrollArea#scroll_job_form {\n"
"    background-color: #F0F4F8;\n"
"    border: none;\n"
"}\n"
"QScrollArea#scroll_job_form > QWidget {\n"
"    background-color: #F0F4F8;\n"
"    border: none;\n"
"}\n"
"QScrollArea#scroll_job_form > QWidget > QWidget {\n"
"    background-color: #F0F4F8;\n"
"    border: none;\n"
"}\n"
"QDateEdit::drop-down { border: none; width: 22px; }")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_root = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_root.setSpacing(0)
        self.horizontalLayout_root.setObjectName(u"horizontalLayout_root")
        self.horizontalLayout_root.setContentsMargins(0, 0, 0, 0)
        self.Left_container = QFrame(self.centralwidget)
        self.Left_container.setObjectName(u"Left_container")
        self.Left_container.setMinimumSize(QSize(66, 0))
        self.Left_container.setMaximumSize(QSize(66, 16777215))
        self.verticalLayout_left = QVBoxLayout(self.Left_container)
        self.verticalLayout_left.setSpacing(2)
        self.verticalLayout_left.setObjectName(u"verticalLayout_left")
        self.verticalLayout_left.setContentsMargins(0, 0, 0, 8)
        self.btn_toggle = QPushButton(self.Left_container)
        self.btn_toggle.setObjectName(u"btn_toggle")
        self.btn_toggle.setMinimumSize(QSize(0, 44))
        icon1 = QIcon()
        icon1.addFile(u"Icons_/menu1.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_toggle.setIcon(icon1)
        self.btn_toggle.setIconSize(QSize(24, 24))

        self.verticalLayout_left.addWidget(self.btn_toggle)

        self.label_logo = QLabel(self.Left_container)
        self.label_logo.setObjectName(u"label_logo")
        self.label_logo.setVisible(False)
        self.label_logo.setAlignment(Qt.AlignCenter)

        self.verticalLayout_left.addWidget(self.label_logo)

        self.btn_home = QPushButton(self.Left_container)
        self.btn_home.setObjectName(u"btn_home")
        self.btn_home.setMinimumSize(QSize(0, 56))
        icon2 = QIcon()
        icon2.addFile(u"Icons_/icon_home_56x56.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_home.setIcon(icon2)
        self.btn_home.setIconSize(QSize(56, 56))
        self.btn_home.setCheckable(True)

        self.verticalLayout_left.addWidget(self.btn_home)

        self.btn_jobs = QPushButton(self.Left_container)
        self.btn_jobs.setObjectName(u"btn_jobs")
        self.btn_jobs.setMinimumSize(QSize(0, 56))
        icon3 = QIcon()
        icon3.addFile(u"Icons_/icon_job_records_56x56.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_jobs.setIcon(icon3)
        self.btn_jobs.setIconSize(QSize(56, 56))
        self.btn_jobs.setCheckable(True)

        self.verticalLayout_left.addWidget(self.btn_jobs)

        self.btn_registrations = QPushButton(self.Left_container)
        self.btn_registrations.setObjectName(u"btn_registrations")
        self.btn_registrations.setMinimumSize(QSize(0, 56))
        icon4 = QIcon()
        icon4.addFile(u"Icons_/icon_registrations_56x56.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_registrations.setIcon(icon4)
        self.btn_registrations.setIconSize(QSize(56, 56))
        self.btn_registrations.setCheckable(True)

        self.verticalLayout_left.addWidget(self.btn_registrations)

        self.frame_registrations_submenu = QFrame(self.Left_container)
        self.frame_registrations_submenu.setObjectName(u"frame_registrations_submenu")
        self.frame_registrations_submenu.setVisible(False)
        self.layout_registrations_submenu = QVBoxLayout(self.frame_registrations_submenu)
        self.layout_registrations_submenu.setSpacing(2)
        self.layout_registrations_submenu.setObjectName(u"layout_registrations_submenu")
        self.layout_registrations_submenu.setContentsMargins(0, 0, 0, 0)
        self.btn_reg_companies = QPushButton(self.frame_registrations_submenu)
        self.btn_reg_companies.setObjectName(u"btn_reg_companies")
        self.btn_reg_companies.setMinimumSize(QSize(0, 56))
        icon5 = QIcon()
        icon5.addFile(u"Icons_/icon_companies_56x56.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_reg_companies.setIcon(icon5)
        self.btn_reg_companies.setIconSize(QSize(56, 56))
        self.btn_reg_companies.setCheckable(True)

        self.layout_registrations_submenu.addWidget(self.btn_reg_companies)

        self.btn_reg_contractors = QPushButton(self.frame_registrations_submenu)
        self.btn_reg_contractors.setObjectName(u"btn_reg_contractors")
        self.btn_reg_contractors.setMinimumSize(QSize(0, 56))
        icon6 = QIcon()
        icon6.addFile(u"Icons_/icon_contractors_56x56.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_reg_contractors.setIcon(icon6)
        self.btn_reg_contractors.setIconSize(QSize(56, 56))
        self.btn_reg_contractors.setCheckable(True)

        self.layout_registrations_submenu.addWidget(self.btn_reg_contractors)

        self.btn_reg_work_types = QPushButton(self.frame_registrations_submenu)
        self.btn_reg_work_types.setObjectName(u"btn_reg_work_types")
        self.btn_reg_work_types.setMinimumSize(QSize(0, 56))
        icon7 = QIcon()
        icon7.addFile(u"Icons_/icon_work_types_56x56.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_reg_work_types.setIcon(icon7)
        self.btn_reg_work_types.setIconSize(QSize(56, 56))
        self.btn_reg_work_types.setCheckable(True)

        self.layout_registrations_submenu.addWidget(self.btn_reg_work_types)

        self.btn_reg_products = QPushButton(self.frame_registrations_submenu)
        self.btn_reg_products.setObjectName(u"btn_reg_products")
        self.btn_reg_products.setMinimumSize(QSize(0, 56))
        icon8 = QIcon()
        icon8.addFile(u"Icons_/icon_products_56x56.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_reg_products.setIcon(icon8)
        self.btn_reg_products.setIconSize(QSize(56, 56))
        self.btn_reg_products.setCheckable(True)

        self.layout_registrations_submenu.addWidget(self.btn_reg_products)


        self.verticalLayout_left.addWidget(self.frame_registrations_submenu)

        self.btn_nav_receivables = QPushButton(self.Left_container)
        self.btn_nav_receivables.setObjectName(u"btn_nav_receivables")
        self.btn_nav_receivables.setMinimumSize(QSize(0, 56))
        self.btn_nav_receivables.setMaximumSize(QSize(16777215, 44))
        icon9 = QIcon()
        icon9.addFile(u"Icons_/icon_receivables_56x56.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_nav_receivables.setIcon(icon9)
        self.btn_nav_receivables.setIconSize(QSize(56, 56))
        self.btn_nav_receivables.setCheckable(True)

        self.verticalLayout_left.addWidget(self.btn_nav_receivables)

        self.btn_customer = QPushButton(self.Left_container)
        self.btn_customer.setObjectName(u"btn_customer")
        self.btn_customer.setMinimumSize(QSize(0, 56))
        icon10 = QIcon()
        icon10.addFile(u"Icons_/icon_customer_56x56.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_customer.setIcon(icon10)
        self.btn_customer.setIconSize(QSize(56, 56))
        self.btn_customer.setCheckable(True)

        self.verticalLayout_left.addWidget(self.btn_customer)

        self.btn_user = QPushButton(self.Left_container)
        self.btn_user.setObjectName(u"btn_user")
        self.btn_user.setMinimumSize(QSize(0, 56))
        icon11 = QIcon()
        icon11.addFile(u"Icons_/icon_user_56x56.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_user.setIcon(icon11)
        self.btn_user.setIconSize(QSize(56, 56))
        self.btn_user.setCheckable(True)

        self.verticalLayout_left.addWidget(self.btn_user)

        self.verticalSpacer_left = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_left.addItem(self.verticalSpacer_left)

        self.btn_settings = QPushButton(self.Left_container)
        self.btn_settings.setObjectName(u"btn_settings")
        self.btn_settings.setMinimumSize(QSize(56, 56))
        self.btn_settings.setMaximumSize(QSize(56, 56))
        icon12 = QIcon()
        icon12.addFile(u"Icons_/icon_settings_56x56.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_settings.setIcon(icon12)
        self.btn_settings.setIconSize(QSize(56, 56))
        self.btn_settings.setCheckable(True)

        self.verticalLayout_left.addWidget(self.btn_settings)


        self.horizontalLayout_root.addWidget(self.Left_container)

        self.Main_container = QFrame(self.centralwidget)
        self.Main_container.setObjectName(u"Main_container")
        self.verticalLayout_main = QVBoxLayout(self.Main_container)
        self.verticalLayout_main.setSpacing(0)
        self.verticalLayout_main.setObjectName(u"verticalLayout_main")
        self.verticalLayout_main.setContentsMargins(0, 0, 0, 0)
        self.Top_frame = QFrame(self.Main_container)
        self.Top_frame.setObjectName(u"Top_frame")
        self.horizontalLayout_top = QHBoxLayout(self.Top_frame)
        self.horizontalLayout_top.setObjectName(u"horizontalLayout_top")
        self.horizontalLayout_top.setContentsMargins(16, 0, 16, 0)
        self.Top_label = QLabel(self.Top_frame)
        self.Top_label.setObjectName(u"Top_label")

        self.horizontalLayout_top.addWidget(self.Top_label)

        self.spacerItem = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_top.addItem(self.spacerItem)

        self.lbl_user = QLabel(self.Top_frame)
        self.lbl_user.setObjectName(u"lbl_user")
        self.lbl_user.setMaximumSize(QSize(160, 16777215))

        self.horizontalLayout_top.addWidget(self.lbl_user)


        self.verticalLayout_main.addWidget(self.Top_frame)

        self.Pages = QStackedWidget(self.Main_container)
        self.Pages.setObjectName(u"Pages")
        self.pg_home = QWidget()
        self.pg_home.setObjectName(u"pg_home")
        self.layout_pg_home_outer = QVBoxLayout(self.pg_home)
        self.layout_pg_home_outer.setObjectName(u"layout_pg_home_outer")
        self.layout_pg_home_outer.setContentsMargins(0, 0, 0, 0)
        self.scroll_home_page = QScrollArea(self.pg_home)
        self.scroll_home_page.setObjectName(u"scroll_home_page")
        self.scroll_home_page.setFrameShape(QFrame.NoFrame)
        self.scroll_home_page.setWidgetResizable(True)
        self.scroll_home_page_contents = QWidget()
        self.scroll_home_page_contents.setObjectName(u"scroll_home_page_contents")
        self.scroll_home_page_contents.setGeometry(QRect(0, 0, 1598, 992))
        self.layout_home_page = QVBoxLayout(self.scroll_home_page_contents)
        self.layout_home_page.setSpacing(16)
        self.layout_home_page.setObjectName(u"layout_home_page")
        self.layout_home_page.setContentsMargins(20, 20, 20, 20)
        self.layout_home_cards_row = QHBoxLayout()
        self.layout_home_cards_row.setSpacing(16)
        self.layout_home_cards_row.setObjectName(u"layout_home_cards_row")
        self.card_home_jobs_month = QFrame(self.scroll_home_page_contents)
        self.card_home_jobs_month.setObjectName(u"card_home_jobs_month")
        self.card_home_jobs_month.setMinimumSize(QSize(0, 100))
        self.card_home_jobs_month.setStyleSheet(u"QFrame#card_home_jobs_month { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout = QVBoxLayout(self.card_home_jobs_month)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.vboxLayout.setContentsMargins(18, 14, 18, 14)
        self.lbl_home_jobs_month_icon = QLabel(self.card_home_jobs_month)
        self.lbl_home_jobs_month_icon.setObjectName(u"lbl_home_jobs_month_icon")

        self.vboxLayout.addWidget(self.lbl_home_jobs_month_icon)

        self.lbl_home_jobs_month_value = QLabel(self.card_home_jobs_month)
        self.lbl_home_jobs_month_value.setObjectName(u"lbl_home_jobs_month_value")

        self.vboxLayout.addWidget(self.lbl_home_jobs_month_value)

        self.lbl_home_jobs_month_label = QLabel(self.card_home_jobs_month)
        self.lbl_home_jobs_month_label.setObjectName(u"lbl_home_jobs_month_label")

        self.vboxLayout.addWidget(self.lbl_home_jobs_month_label)


        self.layout_home_cards_row.addWidget(self.card_home_jobs_month)

        self.card_home_revenue_month = QFrame(self.scroll_home_page_contents)
        self.card_home_revenue_month.setObjectName(u"card_home_revenue_month")
        self.card_home_revenue_month.setMinimumSize(QSize(0, 100))
        self.card_home_revenue_month.setStyleSheet(u"QFrame#card_home_revenue_month { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout1 = QVBoxLayout(self.card_home_revenue_month)
        self.vboxLayout1.setObjectName(u"vboxLayout1")
        self.vboxLayout1.setContentsMargins(18, 14, 18, 14)
        self.lbl_home_revenue_month_icon = QLabel(self.card_home_revenue_month)
        self.lbl_home_revenue_month_icon.setObjectName(u"lbl_home_revenue_month_icon")

        self.vboxLayout1.addWidget(self.lbl_home_revenue_month_icon)

        self.lbl_home_revenue_month_value = QLabel(self.card_home_revenue_month)
        self.lbl_home_revenue_month_value.setObjectName(u"lbl_home_revenue_month_value")

        self.vboxLayout1.addWidget(self.lbl_home_revenue_month_value)

        self.lbl_home_revenue_month_label = QLabel(self.card_home_revenue_month)
        self.lbl_home_revenue_month_label.setObjectName(u"lbl_home_revenue_month_label")

        self.vboxLayout1.addWidget(self.lbl_home_revenue_month_label)


        self.layout_home_cards_row.addWidget(self.card_home_revenue_month)

        self.card_home_overdue = QFrame(self.scroll_home_page_contents)
        self.card_home_overdue.setObjectName(u"card_home_overdue")
        self.card_home_overdue.setMinimumSize(QSize(0, 100))
        self.card_home_overdue.setStyleSheet(u"QFrame#card_home_overdue { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout2 = QVBoxLayout(self.card_home_overdue)
        self.vboxLayout2.setObjectName(u"vboxLayout2")
        self.vboxLayout2.setContentsMargins(18, 14, 18, 14)
        self.lbl_home_overdue_icon = QLabel(self.card_home_overdue)
        self.lbl_home_overdue_icon.setObjectName(u"lbl_home_overdue_icon")

        self.vboxLayout2.addWidget(self.lbl_home_overdue_icon)

        self.lbl_home_overdue_value = QLabel(self.card_home_overdue)
        self.lbl_home_overdue_value.setObjectName(u"lbl_home_overdue_value")

        self.vboxLayout2.addWidget(self.lbl_home_overdue_value)

        self.lbl_home_overdue_label = QLabel(self.card_home_overdue)
        self.lbl_home_overdue_label.setObjectName(u"lbl_home_overdue_label")

        self.vboxLayout2.addWidget(self.lbl_home_overdue_label)


        self.layout_home_cards_row.addWidget(self.card_home_overdue)

        self.card_home_pending_jobs = QFrame(self.scroll_home_page_contents)
        self.card_home_pending_jobs.setObjectName(u"card_home_pending_jobs")
        self.card_home_pending_jobs.setMinimumSize(QSize(0, 100))
        self.card_home_pending_jobs.setStyleSheet(u"QFrame#card_home_pending_jobs { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout3 = QVBoxLayout(self.card_home_pending_jobs)
        self.vboxLayout3.setObjectName(u"vboxLayout3")
        self.vboxLayout3.setContentsMargins(18, 14, 18, 14)
        self.lbl_home_pending_jobs_icon = QLabel(self.card_home_pending_jobs)
        self.lbl_home_pending_jobs_icon.setObjectName(u"lbl_home_pending_jobs_icon")

        self.vboxLayout3.addWidget(self.lbl_home_pending_jobs_icon)

        self.lbl_home_pending_jobs_value = QLabel(self.card_home_pending_jobs)
        self.lbl_home_pending_jobs_value.setObjectName(u"lbl_home_pending_jobs_value")

        self.vboxLayout3.addWidget(self.lbl_home_pending_jobs_value)

        self.lbl_home_pending_jobs_label = QLabel(self.card_home_pending_jobs)
        self.lbl_home_pending_jobs_label.setObjectName(u"lbl_home_pending_jobs_label")

        self.vboxLayout3.addWidget(self.lbl_home_pending_jobs_label)


        self.layout_home_cards_row.addWidget(self.card_home_pending_jobs)


        self.layout_home_page.addLayout(self.layout_home_cards_row)

        self.layout_home_actions_row = QHBoxLayout()
        self.layout_home_actions_row.setSpacing(12)
        self.layout_home_actions_row.setObjectName(u"layout_home_actions_row")
        self.btn_home_new_job = QPushButton(self.scroll_home_page_contents)
        self.btn_home_new_job.setObjectName(u"btn_home_new_job")
        self.btn_home_new_job.setMinimumSize(QSize(0, 46))
        self.btn_home_new_job.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_home_new_job.setStyleSheet(u"QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 8px; font-size: 13px; font-weight: 700; } QPushButton:hover { background-color: #1E88E5; }")

        self.layout_home_actions_row.addWidget(self.btn_home_new_job)

        self.btn_home_generate_invoices = QPushButton(self.scroll_home_page_contents)
        self.btn_home_generate_invoices.setObjectName(u"btn_home_generate_invoices")
        self.btn_home_generate_invoices.setMinimumSize(QSize(0, 46))
        self.btn_home_generate_invoices.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_home_generate_invoices.setStyleSheet(u"QPushButton { background-color: #37474F; color: #FFFFFF; border: none; border-radius: 8px; font-size: 13px; font-weight: 700; } QPushButton:hover { background-color: #546E7A; }")

        self.layout_home_actions_row.addWidget(self.btn_home_generate_invoices)

        self.btn_home_schedule = QPushButton(self.scroll_home_page_contents)
        self.btn_home_schedule.setObjectName(u"btn_home_schedule")
        self.btn_home_schedule.setMinimumSize(QSize(0, 46))
        self.btn_home_schedule.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_home_schedule.setStyleSheet(u"QPushButton { background-color: #37474F; color: #FFFFFF; border: none; border-radius: 8px; font-size: 13px; font-weight: 700; } QPushButton:hover { background-color: #546E7A; }")

        self.layout_home_actions_row.addWidget(self.btn_home_schedule)

        self.btn_home_new_customer = QPushButton(self.scroll_home_page_contents)
        self.btn_home_new_customer.setObjectName(u"btn_home_new_customer")
        self.btn_home_new_customer.setMinimumSize(QSize(0, 46))
        self.btn_home_new_customer.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_home_new_customer.setStyleSheet(u"QPushButton { background-color: #37474F; color: #FFFFFF; border: none; border-radius: 8px; font-size: 13px; font-weight: 700; } QPushButton:hover { background-color: #546E7A; }")

        self.layout_home_actions_row.addWidget(self.btn_home_new_customer)


        self.layout_home_page.addLayout(self.layout_home_actions_row)

        self.layout_home_bottom_row = QHBoxLayout()
        self.layout_home_bottom_row.setSpacing(16)
        self.layout_home_bottom_row.setObjectName(u"layout_home_bottom_row")
        self.layout_home_recent_jobs_col = QVBoxLayout()
        self.layout_home_recent_jobs_col.setObjectName(u"layout_home_recent_jobs_col")
        self.lbl_home_recent_jobs_title = QLabel(self.scroll_home_page_contents)
        self.lbl_home_recent_jobs_title.setObjectName(u"lbl_home_recent_jobs_title")
        self.lbl_home_recent_jobs_title.setStyleSheet(u"font-size:14px; font-weight:700; color:#1A1F36; background:transparent;")

        self.layout_home_recent_jobs_col.addWidget(self.lbl_home_recent_jobs_title)

        self.table_home_recent_jobs = QTableWidget(self.scroll_home_page_contents)
        if (self.table_home_recent_jobs.columnCount() < 5):
            self.table_home_recent_jobs.setColumnCount(5)
        __qtablewidgetitem = QTableWidgetItem()
        self.table_home_recent_jobs.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table_home_recent_jobs.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.table_home_recent_jobs.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.table_home_recent_jobs.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.table_home_recent_jobs.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        self.table_home_recent_jobs.setObjectName(u"table_home_recent_jobs")
        self.table_home_recent_jobs.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_home_recent_jobs.setAlternatingRowColors(True)
        self.table_home_recent_jobs.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_home_recent_jobs.setColumnCount(5)
        self.table_home_recent_jobs.horizontalHeader().setStretchLastSection(True)

        self.layout_home_recent_jobs_col.addWidget(self.table_home_recent_jobs)


        self.layout_home_bottom_row.addLayout(self.layout_home_recent_jobs_col)

        self.layout_home_chart_col = QVBoxLayout()
        self.layout_home_chart_col.setObjectName(u"layout_home_chart_col")
        self.lbl_home_chart_title = QLabel(self.scroll_home_page_contents)
        self.lbl_home_chart_title.setObjectName(u"lbl_home_chart_title")
        self.lbl_home_chart_title.setStyleSheet(u"font-size:14px; font-weight:700; color:#1A1F36; background:transparent;")

        self.layout_home_chart_col.addWidget(self.lbl_home_chart_title)

        self.frame_home_revenue_chart = QFrame(self.scroll_home_page_contents)
        self.frame_home_revenue_chart.setObjectName(u"frame_home_revenue_chart")
        self.frame_home_revenue_chart.setMinimumSize(QSize(0, 220))
        self.frame_home_revenue_chart.setStyleSheet(u"QFrame#frame_home_revenue_chart { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.layout_home_revenue_chart = QHBoxLayout(self.frame_home_revenue_chart)
        self.layout_home_revenue_chart.setSpacing(10)
        self.layout_home_revenue_chart.setObjectName(u"layout_home_revenue_chart")
        self.layout_home_revenue_chart.setContentsMargins(16, 16, 16, 12)

        self.layout_home_chart_col.addWidget(self.frame_home_revenue_chart)


        self.layout_home_bottom_row.addLayout(self.layout_home_chart_col)


        self.layout_home_page.addLayout(self.layout_home_bottom_row)

        self.lbl_home_work_types_title = QLabel(self.scroll_home_page_contents)
        self.lbl_home_work_types_title.setObjectName(u"lbl_home_work_types_title")
        self.lbl_home_work_types_title.setStyleSheet(u"font-size:14px; font-weight:700; color:#1A1F36; background:transparent;")

        self.layout_home_page.addWidget(self.lbl_home_work_types_title)

        self.layout_home_work_type_cards = QHBoxLayout()
        self.layout_home_work_type_cards.setSpacing(16)
        self.layout_home_work_type_cards.setObjectName(u"layout_home_work_type_cards")
        self.card_home_work_type_1 = QFrame(self.scroll_home_page_contents)
        self.card_home_work_type_1.setObjectName(u"card_home_work_type_1")
        self.card_home_work_type_1.setMinimumSize(QSize(0, 90))
        self.card_home_work_type_1.setStyleSheet(u"QFrame#card_home_work_type_1 { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout4 = QVBoxLayout(self.card_home_work_type_1)
        self.vboxLayout4.setObjectName(u"vboxLayout4")
        self.vboxLayout4.setContentsMargins(16, 12, 16, 12)
        self.lbl_home_work_type_1_value = QLabel(self.card_home_work_type_1)
        self.lbl_home_work_type_1_value.setObjectName(u"lbl_home_work_type_1_value")

        self.vboxLayout4.addWidget(self.lbl_home_work_type_1_value)

        self.lbl_home_work_type_1_label = QLabel(self.card_home_work_type_1)
        self.lbl_home_work_type_1_label.setObjectName(u"lbl_home_work_type_1_label")

        self.vboxLayout4.addWidget(self.lbl_home_work_type_1_label)


        self.layout_home_work_type_cards.addWidget(self.card_home_work_type_1)

        self.card_home_work_type_2 = QFrame(self.scroll_home_page_contents)
        self.card_home_work_type_2.setObjectName(u"card_home_work_type_2")
        self.card_home_work_type_2.setMinimumSize(QSize(0, 90))
        self.card_home_work_type_2.setStyleSheet(u"QFrame#card_home_work_type_2 { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout5 = QVBoxLayout(self.card_home_work_type_2)
        self.vboxLayout5.setObjectName(u"vboxLayout5")
        self.vboxLayout5.setContentsMargins(16, 12, 16, 12)
        self.lbl_home_work_type_2_value = QLabel(self.card_home_work_type_2)
        self.lbl_home_work_type_2_value.setObjectName(u"lbl_home_work_type_2_value")

        self.vboxLayout5.addWidget(self.lbl_home_work_type_2_value)

        self.lbl_home_work_type_2_label = QLabel(self.card_home_work_type_2)
        self.lbl_home_work_type_2_label.setObjectName(u"lbl_home_work_type_2_label")

        self.vboxLayout5.addWidget(self.lbl_home_work_type_2_label)


        self.layout_home_work_type_cards.addWidget(self.card_home_work_type_2)

        self.card_home_work_type_3 = QFrame(self.scroll_home_page_contents)
        self.card_home_work_type_3.setObjectName(u"card_home_work_type_3")
        self.card_home_work_type_3.setMinimumSize(QSize(0, 90))
        self.card_home_work_type_3.setStyleSheet(u"QFrame#card_home_work_type_3 { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout6 = QVBoxLayout(self.card_home_work_type_3)
        self.vboxLayout6.setObjectName(u"vboxLayout6")
        self.vboxLayout6.setContentsMargins(16, 12, 16, 12)
        self.lbl_home_work_type_3_value = QLabel(self.card_home_work_type_3)
        self.lbl_home_work_type_3_value.setObjectName(u"lbl_home_work_type_3_value")

        self.vboxLayout6.addWidget(self.lbl_home_work_type_3_value)

        self.lbl_home_work_type_3_label = QLabel(self.card_home_work_type_3)
        self.lbl_home_work_type_3_label.setObjectName(u"lbl_home_work_type_3_label")

        self.vboxLayout6.addWidget(self.lbl_home_work_type_3_label)


        self.layout_home_work_type_cards.addWidget(self.card_home_work_type_3)

        self.card_home_work_type_4 = QFrame(self.scroll_home_page_contents)
        self.card_home_work_type_4.setObjectName(u"card_home_work_type_4")
        self.card_home_work_type_4.setMinimumSize(QSize(0, 90))
        self.card_home_work_type_4.setStyleSheet(u"QFrame#card_home_work_type_4 { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout7 = QVBoxLayout(self.card_home_work_type_4)
        self.vboxLayout7.setObjectName(u"vboxLayout7")
        self.vboxLayout7.setContentsMargins(16, 12, 16, 12)
        self.lbl_home_work_type_4_value = QLabel(self.card_home_work_type_4)
        self.lbl_home_work_type_4_value.setObjectName(u"lbl_home_work_type_4_value")

        self.vboxLayout7.addWidget(self.lbl_home_work_type_4_value)

        self.lbl_home_work_type_4_label = QLabel(self.card_home_work_type_4)
        self.lbl_home_work_type_4_label.setObjectName(u"lbl_home_work_type_4_label")

        self.vboxLayout7.addWidget(self.lbl_home_work_type_4_label)


        self.layout_home_work_type_cards.addWidget(self.card_home_work_type_4)


        self.layout_home_page.addLayout(self.layout_home_work_type_cards)

        self.frame_home_work_types_chart = QFrame(self.scroll_home_page_contents)
        self.frame_home_work_types_chart.setObjectName(u"frame_home_work_types_chart")
        self.frame_home_work_types_chart.setMinimumSize(QSize(0, 160))
        self.frame_home_work_types_chart.setStyleSheet(u"QFrame#frame_home_work_types_chart { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.layout_home_work_types_chart = QHBoxLayout(self.frame_home_work_types_chart)
        self.layout_home_work_types_chart.setSpacing(10)
        self.layout_home_work_types_chart.setObjectName(u"layout_home_work_types_chart")
        self.layout_home_work_types_chart.setContentsMargins(16, 16, 16, 12)

        self.layout_home_page.addWidget(self.frame_home_work_types_chart)

        self.scroll_home_page.setWidget(self.scroll_home_page_contents)

        self.layout_pg_home_outer.addWidget(self.scroll_home_page)

        self.Pages.addWidget(self.pg_home)
        self.pg_jobs = QWidget()
        self.pg_jobs.setObjectName(u"pg_jobs")
        self.layout_jobs = QVBoxLayout(self.pg_jobs)
        self.layout_jobs.setSpacing(0)
        self.layout_jobs.setObjectName(u"layout_jobs")
        self.layout_jobs.setContentsMargins(0, 0, 0, 0)
        self.tabWidget_jobs = QTabWidget(self.pg_jobs)
        self.tabWidget_jobs.setObjectName(u"tabWidget_jobs")
        self.tab_jobs_master = QWidget()
        self.tab_jobs_master.setObjectName(u"tab_jobs_master")
        self.layout_tab_jobs_master = QHBoxLayout(self.tab_jobs_master)
        self.layout_tab_jobs_master.setSpacing(16)
        self.layout_tab_jobs_master.setObjectName(u"layout_tab_jobs_master")
        self.layout_tab_jobs_master.setContentsMargins(16, 16, 16, 16)
        self.frame_jobs_left_panel = QFrame(self.tab_jobs_master)
        self.frame_jobs_left_panel.setObjectName(u"frame_jobs_left_panel")
        self.frame_jobs_left_panel.setMaximumSize(QSize(460, 16777215))
        self.layout_jobs_left_panel = QVBoxLayout(self.frame_jobs_left_panel)
        self.layout_jobs_left_panel.setSpacing(10)
        self.layout_jobs_left_panel.setObjectName(u"layout_jobs_left_panel")
        self.layout_jobs_left_panel.setContentsMargins(0, 0, 0, 0)
        self.layout_jobs_row_search = QHBoxLayout()
        self.layout_jobs_row_search.setSpacing(8)
        self.layout_jobs_row_search.setObjectName(u"layout_jobs_row_search")
        self.txt_search_jobs = QLineEdit(self.frame_jobs_left_panel)
        self.txt_search_jobs.setObjectName(u"txt_search_jobs")
        self.txt_search_jobs.setMinimumSize(QSize(280, 36))

        self.layout_jobs_row_search.addWidget(self.txt_search_jobs)


        self.layout_jobs_left_panel.addLayout(self.layout_jobs_row_search)

        self.layout_jobs_row_filters = QHBoxLayout()
        self.layout_jobs_row_filters.setSpacing(8)
        self.layout_jobs_row_filters.setObjectName(u"layout_jobs_row_filters")
        self.cmb_filter_status = QComboBox(self.frame_jobs_left_panel)
        self.cmb_filter_status.addItem("")
        self.cmb_filter_status.addItem("")
        self.cmb_filter_status.addItem("")
        self.cmb_filter_status.addItem("")
        self.cmb_filter_status.addItem("")
        self.cmb_filter_status.addItem("")
        self.cmb_filter_status.setObjectName(u"cmb_filter_status")
        self.cmb_filter_status.setMinimumSize(QSize(140, 46))
        self.cmb_filter_status.setMaximumSize(QSize(16777215, 16777215))

        self.layout_jobs_row_filters.addWidget(self.cmb_filter_status)

        self.date_filter_from = QDateEdit(self.frame_jobs_left_panel)
        self.date_filter_from.setObjectName(u"date_filter_from")
        self.date_filter_from.setMinimumSize(QSize(130, 36))
        self.date_filter_from.setMaximumSize(QSize(16777215, 36))
        self.date_filter_from.setCalendarPopup(True)

        self.layout_jobs_row_filters.addWidget(self.date_filter_from)

        self.date_filter_to = QDateEdit(self.frame_jobs_left_panel)
        self.date_filter_to.setObjectName(u"date_filter_to")
        self.date_filter_to.setMinimumSize(QSize(130, 36))
        self.date_filter_to.setMaximumSize(QSize(16777215, 36))
        self.date_filter_to.setCalendarPopup(True)

        self.layout_jobs_row_filters.addWidget(self.date_filter_to)


        self.layout_jobs_left_panel.addLayout(self.layout_jobs_row_filters)

        self.layout_jobs_row_export = QHBoxLayout()
        self.layout_jobs_row_export.setSpacing(8)
        self.layout_jobs_row_export.setObjectName(u"layout_jobs_row_export")
        self.btn_refresh_jobs = QPushButton(self.frame_jobs_left_panel)
        self.btn_refresh_jobs.setObjectName(u"btn_refresh_jobs")
        self.btn_refresh_jobs.setMinimumSize(QSize(90, 36))
        self.btn_refresh_jobs.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_jobs_row_export.addWidget(self.btn_refresh_jobs)

        self.btn_export_excel_jobs = QPushButton(self.frame_jobs_left_panel)
        self.btn_export_excel_jobs.setObjectName(u"btn_export_excel_jobs")
        self.btn_export_excel_jobs.setMinimumSize(QSize(110, 36))
        self.btn_export_excel_jobs.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_jobs_row_export.addWidget(self.btn_export_excel_jobs)

        self.btn_export_pdf_jobs = QPushButton(self.frame_jobs_left_panel)
        self.btn_export_pdf_jobs.setObjectName(u"btn_export_pdf_jobs")
        self.btn_export_pdf_jobs.setMinimumSize(QSize(100, 36))
        self.btn_export_pdf_jobs.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_jobs_row_export.addWidget(self.btn_export_pdf_jobs)


        self.layout_jobs_left_panel.addLayout(self.layout_jobs_row_export)

        self.layout_jobs_row_actions = QHBoxLayout()
        self.layout_jobs_row_actions.setSpacing(8)
        self.layout_jobs_row_actions.setObjectName(u"layout_jobs_row_actions")
        self.btn_split_daily_total = QPushButton(self.frame_jobs_left_panel)
        self.btn_split_daily_total.setObjectName(u"btn_split_daily_total")
        self.btn_split_daily_total.setMinimumSize(QSize(150, 36))
        self.btn_split_daily_total.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_jobs_row_actions.addWidget(self.btn_split_daily_total)

        self.btn_view_project = QPushButton(self.frame_jobs_left_panel)
        self.btn_view_project.setObjectName(u"btn_view_project")
        self.btn_view_project.setMinimumSize(QSize(0, 36))
        self.btn_view_project.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_jobs_row_actions.addWidget(self.btn_view_project)


        self.layout_jobs_left_panel.addLayout(self.layout_jobs_row_actions)

        self.btn_clean_empty_job_codes = QPushButton(self.frame_jobs_left_panel)
        self.btn_clean_empty_job_codes.setObjectName(u"btn_clean_empty_job_codes")
        self.btn_clean_empty_job_codes.setMinimumSize(QSize(0, 34))
        self.btn_clean_empty_job_codes.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_clean_empty_job_codes.setStyleSheet(u"QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; border-radius: 6px; font-size: 12px; font-weight: 600; } QPushButton:hover { background-color: #E1E8F0; }")

        self.layout_jobs_left_panel.addWidget(self.btn_clean_empty_job_codes)

        self.btn_toggle_table_expanded = QPushButton(self.frame_jobs_left_panel)
        self.btn_toggle_table_expanded.setObjectName(u"btn_toggle_table_expanded")
        self.btn_toggle_table_expanded.setMinimumSize(QSize(0, 34))
        self.btn_toggle_table_expanded.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle_table_expanded.setStyleSheet(u"QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; border-radius: 6px; font-size: 12px; font-weight: 600; } QPushButton:hover { background-color: #E1E8F0; }")

        self.layout_jobs_left_panel.addWidget(self.btn_toggle_table_expanded)

        self.table_work_days = QTableWidget(self.frame_jobs_left_panel)
        if (self.table_work_days.columnCount() < 16):
            self.table_work_days.setColumnCount(16)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(0, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(1, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(2, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(3, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(4, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(5, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(6, __qtablewidgetitem11)
        __qtablewidgetitem12 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(7, __qtablewidgetitem12)
        __qtablewidgetitem13 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(8, __qtablewidgetitem13)
        __qtablewidgetitem14 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(9, __qtablewidgetitem14)
        __qtablewidgetitem15 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(10, __qtablewidgetitem15)
        __qtablewidgetitem16 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(11, __qtablewidgetitem16)
        __qtablewidgetitem17 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(12, __qtablewidgetitem17)
        __qtablewidgetitem18 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(13, __qtablewidgetitem18)
        __qtablewidgetitem19 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(14, __qtablewidgetitem19)
        __qtablewidgetitem20 = QTableWidgetItem()
        self.table_work_days.setHorizontalHeaderItem(15, __qtablewidgetitem20)
        self.table_work_days.setObjectName(u"table_work_days")
        self.table_work_days.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table_work_days.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_work_days.setAlternatingRowColors(True)
        self.table_work_days.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_work_days.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_work_days.setSortingEnabled(True)
        self.table_work_days.setColumnCount(16)

        self.layout_jobs_left_panel.addWidget(self.table_work_days)


        self.layout_tab_jobs_master.addWidget(self.frame_jobs_left_panel)

        self.frame_jobs_right_panel = QFrame(self.tab_jobs_master)
        self.frame_jobs_right_panel.setObjectName(u"frame_jobs_right_panel")
        self.layout_jobs_right_panel = QVBoxLayout(self.frame_jobs_right_panel)
        self.layout_jobs_right_panel.setSpacing(0)
        self.layout_jobs_right_panel.setObjectName(u"layout_jobs_right_panel")
        self.layout_jobs_right_panel.setContentsMargins(0, 0, 0, 0)
        self.card_header_jobs = QFrame(self.frame_jobs_right_panel)
        self.card_header_jobs.setObjectName(u"card_header_jobs")
        self.hboxLayout = QHBoxLayout(self.card_header_jobs)
        self.hboxLayout.setObjectName(u"hboxLayout")
        self.hboxLayout.setContentsMargins(20, -1, -1, -1)
        self.btn_new_job = QPushButton(self.card_header_jobs)
        self.btn_new_job.setObjectName(u"btn_new_job")
        self.btn_new_job.setMinimumSize(QSize(0, 32))
        self.btn_new_job.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new_job.setStyleSheet(u"QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 6px; padding: 4px 12px; font-size: 12px; font-weight: 600; } QPushButton:hover { background-color: #1E88E5; }")

        self.hboxLayout.addWidget(self.btn_new_job)

        self.btn_job_go_to_expense = QPushButton(self.card_header_jobs)
        self.btn_job_go_to_expense.setObjectName(u"btn_job_go_to_expense")
        self.btn_job_go_to_expense.setMinimumSize(QSize(0, 32))
        self.btn_job_go_to_expense.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_job_go_to_expense.setStyleSheet(u"QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; border-radius: 6px; padding: 6px 14px; font-size: 12px; font-weight: 600; } QPushButton:hover { background-color: #E1E8F0; }")

        self.hboxLayout.addWidget(self.btn_job_go_to_expense)

        self.lbl_form_title = QLabel(self.card_header_jobs)
        self.lbl_form_title.setObjectName(u"lbl_form_title")

        self.hboxLayout.addWidget(self.lbl_form_title)

        self.spacerItem1 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout.addItem(self.spacerItem1)

        self.lbl_job_id_display = QLabel(self.card_header_jobs)
        self.lbl_job_id_display.setObjectName(u"lbl_job_id_display")

        self.hboxLayout.addWidget(self.lbl_job_id_display)

        self.btn_toggle_client_drawer = QPushButton(self.card_header_jobs)
        self.btn_toggle_client_drawer.setObjectName(u"btn_toggle_client_drawer")
        self.btn_toggle_client_drawer.setMinimumSize(QSize(0, 32))
        self.btn_toggle_client_drawer.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle_client_drawer.setStyleSheet(u"QPushButton { background-color: rgba(255,255,255,0.12); color: #FFFFFF; border: none; border-radius: 6px; padding: 6px 14px; font-size: 12px; font-weight: 600; } QPushButton:hover { background-color: rgba(255,255,255,0.22); }")

        self.hboxLayout.addWidget(self.btn_toggle_client_drawer)

        self.spacer_lbl = QLabel(self.card_header_jobs)
        self.spacer_lbl.setObjectName(u"spacer_lbl")

        self.hboxLayout.addWidget(self.spacer_lbl)


        self.layout_jobs_right_panel.addWidget(self.card_header_jobs)

        self.frame_job_card = QFrame(self.frame_jobs_right_panel)
        self.frame_job_card.setObjectName(u"frame_job_card")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.frame_job_card.sizePolicy().hasHeightForWidth())
        self.frame_job_card.setSizePolicy(sizePolicy)
        self.frame_job_card.setMaximumSize(QSize(16777215, 16777215))
        self.layout_job_card = QVBoxLayout(self.frame_job_card)
        self.layout_job_card.setSpacing(0)
        self.layout_job_card.setObjectName(u"layout_job_card")
        self.layout_job_card.setContentsMargins(0, 0, 0, 0)
        self.scroll_job_form = QScrollArea(self.frame_job_card)
        self.scroll_job_form.setObjectName(u"scroll_job_form")
        self.scroll_job_form.setMinimumSize(QSize(0, 36))
        self.scroll_job_form.setFrameShape(QFrame.NoFrame)
        self.scroll_job_form.setWidgetResizable(True)
        self.frame_job_body = QFrame()
        self.frame_job_body.setObjectName(u"frame_job_body")
        self.frame_job_body.setGeometry(QRect(0, 0, 1064, 1021))
        self.layout_job_body_cards = QVBoxLayout(self.frame_job_body)
        self.layout_job_body_cards.setSpacing(24)
        self.layout_job_body_cards.setObjectName(u"layout_job_body_cards")
        self.layout_job_body_cards.setContentsMargins(0, 0, 0, 0)
        self.frame_card_job = QFrame(self.frame_job_body)
        self.frame_card_job.setObjectName(u"frame_card_job")
        self.layout_frame_card_job = QVBoxLayout(self.frame_card_job)
        self.layout_frame_card_job.setSpacing(0)
        self.layout_frame_card_job.setObjectName(u"layout_frame_card_job")
        self.layout_frame_card_job.setContentsMargins(0, 20, 0, 0)
        self.card_header_job_info = QFrame(self.frame_card_job)
        self.card_header_job_info.setObjectName(u"card_header_job_info")
        self.card_header_job_info.setStyleSheet(u"QFrame#card_header_job_info { border-top-left-radius:10px; border-top-right-radius:10px; border-bottom-left-radius:0px; border-bottom-right-radius:0px; }")
        self.formLayout = QFormLayout(self.card_header_job_info)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(20, 12, -1, 20)
        self.lbl_job_info_title = QLabel(self.card_header_job_info)
        self.lbl_job_info_title.setObjectName(u"lbl_job_info_title")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lbl_job_info_title)


        self.layout_frame_card_job.addWidget(self.card_header_job_info)

        self.frame_job_info_body = QFrame(self.frame_card_job)
        self.frame_job_info_body.setObjectName(u"frame_job_info_body")
        self.frame_job_info_body.setStyleSheet(u"QFrame#frame_job_info_body { border-top-left-radius:0px; border-top-right-radius:0px; border-bottom-left-radius:10px; border-bottom-right-radius:10px; }")
        self.grid_job_info = QGridLayout(self.frame_job_info_body)
        self.grid_job_info.setObjectName(u"grid_job_info")
        self.grid_job_info.setHorizontalSpacing(12)
        self.grid_job_info.setVerticalSpacing(8)
        self.grid_job_info.setContentsMargins(20, 16, 26, 24)
        self.lbl_work_date = QLabel(self.frame_job_info_body)
        self.lbl_work_date.setObjectName(u"lbl_work_date")

        self.grid_job_info.addWidget(self.lbl_work_date, 0, 0, 1, 1)

        self.lbl_job_code = QLabel(self.frame_job_info_body)
        self.lbl_job_code.setObjectName(u"lbl_job_code")

        self.grid_job_info.addWidget(self.lbl_job_code, 0, 1, 1, 1)

        self.lbl_payment = QLabel(self.frame_job_info_body)
        self.lbl_payment.setObjectName(u"lbl_payment")

        self.grid_job_info.addWidget(self.lbl_payment, 0, 3, 1, 1)

        self.date_work_date = QDateEdit(self.frame_job_info_body)
        self.date_work_date.setObjectName(u"date_work_date")
        self.date_work_date.setMinimumSize(QSize(140, 36))
        self.date_work_date.setMaximumSize(QSize(140, 36))
        self.date_work_date.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")
        self.date_work_date.setCalendarPopup(True)

        self.grid_job_info.addWidget(self.date_work_date, 1, 0, 1, 1)

        self.layout_job_code_field_row = QHBoxLayout()
        self.layout_job_code_field_row.setSpacing(8)
        self.layout_job_code_field_row.setObjectName(u"layout_job_code_field_row")
        self.cmb_job_code = QComboBox(self.frame_job_info_body)
        self.cmb_job_code.setObjectName(u"cmb_job_code")
        self.cmb_job_code.setMinimumSize(QSize(160, 46))
        self.cmb_job_code.setEditable(True)
        self.cmb_job_code.setInsertPolicy(QComboBox.NoInsert)

        self.layout_job_code_field_row.addWidget(self.cmb_job_code)

        self.btn_generate_job_code = QPushButton(self.frame_job_info_body)
        self.btn_generate_job_code.setObjectName(u"btn_generate_job_code")
        self.btn_generate_job_code.setMinimumSize(QSize(0, 36))
        self.btn_generate_job_code.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_generate_job_code.setStyleSheet(u"QPushButton { background-color: #37474F; color: #FFFFFF; border: none; border-radius: 6px; padding: 0 14px; font-size: 12px; font-weight: 600; } QPushButton:hover { background-color: #546E7A; }")

        self.layout_job_code_field_row.addWidget(self.btn_generate_job_code)

        self.lbl_days_worked_value = QLabel(self.frame_job_info_body)
        self.lbl_days_worked_value.setObjectName(u"lbl_days_worked_value")
        self.lbl_days_worked_value.setMinimumSize(QSize(0, 30))
        self.lbl_days_worked_value.setStyleSheet(u"font-size:16px; font-weight:800; color:#1565C0; background:transparent;")

        self.layout_job_code_field_row.addWidget(self.lbl_days_worked_value)


        self.grid_job_info.addLayout(self.layout_job_code_field_row, 1, 1, 1, 2)

        self.cmb_payment = QComboBox(self.frame_job_info_body)
        self.cmb_payment.addItem("")
        self.cmb_payment.addItem("")
        self.cmb_payment.setObjectName(u"cmb_payment")
        self.cmb_payment.setMinimumSize(QSize(140, 46))
        self.cmb_payment.setMaximumSize(QSize(140, 36))
        self.cmb_payment.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_job_info.addWidget(self.cmb_payment, 1, 3, 1, 1)

        self.lbl_contractor = QLabel(self.frame_job_info_body)
        self.lbl_contractor.setObjectName(u"lbl_contractor")

        self.grid_job_info.addWidget(self.lbl_contractor, 2, 0, 1, 1)

        self.lbl_company_form = QLabel(self.frame_job_info_body)
        self.lbl_company_form.setObjectName(u"lbl_company_form")

        self.grid_job_info.addWidget(self.lbl_company_form, 2, 1, 1, 1)

        self.lbl_status_form = QLabel(self.frame_job_info_body)
        self.lbl_status_form.setObjectName(u"lbl_status_form")

        self.grid_job_info.addWidget(self.lbl_status_form, 2, 2, 1, 1)

        self.lbl_value = QLabel(self.frame_job_info_body)
        self.lbl_value.setObjectName(u"lbl_value")

        self.grid_job_info.addWidget(self.lbl_value, 2, 3, 1, 1)

        self.cmb_contractor = QComboBox(self.frame_job_info_body)
        self.cmb_contractor.setObjectName(u"cmb_contractor")
        self.cmb_contractor.setMinimumSize(QSize(190, 46))
        self.cmb_contractor.setMaximumSize(QSize(190, 36))
        self.cmb_contractor.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_job_info.addWidget(self.cmb_contractor, 3, 0, 1, 1)

        self.cmb_company_form = QComboBox(self.frame_job_info_body)
        self.cmb_company_form.setObjectName(u"cmb_company_form")
        self.cmb_company_form.setMinimumSize(QSize(190, 46))
        self.cmb_company_form.setMaximumSize(QSize(190, 36))
        self.cmb_company_form.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_job_info.addWidget(self.cmb_company_form, 3, 1, 1, 1)

        self.cmb_status_form = QComboBox(self.frame_job_info_body)
        self.cmb_status_form.addItem("")
        self.cmb_status_form.addItem("")
        self.cmb_status_form.addItem("")
        self.cmb_status_form.addItem("")
        self.cmb_status_form.addItem("")
        self.cmb_status_form.setObjectName(u"cmb_status_form")
        self.cmb_status_form.setMinimumSize(QSize(150, 46))
        self.cmb_status_form.setMaximumSize(QSize(100, 36))
        self.cmb_status_form.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_job_info.addWidget(self.cmb_status_form, 3, 2, 1, 1)

        self.dspn_value = QDoubleSpinBox(self.frame_job_info_body)
        self.dspn_value.setObjectName(u"dspn_value")
        self.dspn_value.setMinimumSize(QSize(132, 36))
        self.dspn_value.setMaximumSize(QSize(132, 36))
        self.dspn_value.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")
        self.dspn_value.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_value.setDecimals(2)
        self.dspn_value.setMinimum(0.000000000000000)
        self.dspn_value.setMaximum(999999.989999999990687)
        self.dspn_value.setSingleStep(1.000000000000000)
        self.dspn_value.setProperty(u"groupSeparatorShown", True)

        self.grid_job_info.addWidget(self.dspn_value, 3, 3, 1, 1)


        self.layout_frame_card_job.addWidget(self.frame_job_info_body)


        self.layout_job_body_cards.addWidget(self.frame_card_job)

        self.layout_work_client_row = QHBoxLayout()
        self.layout_work_client_row.setSpacing(24)
        self.layout_work_client_row.setObjectName(u"layout_work_client_row")
        self.layout_work_client_row.setContentsMargins(0, 0, 20, -1)
        self.layout_col_work_types = QVBoxLayout()
        self.layout_col_work_types.setSpacing(0)
        self.layout_col_work_types.setObjectName(u"layout_col_work_types")
        self.layout_col_work_types.setContentsMargins(0, 0, 0, 0)
        self.frame_card_work = QFrame(self.frame_job_body)
        self.frame_card_work.setObjectName(u"frame_card_work")
        self.layout_frame_card_work = QVBoxLayout(self.frame_card_work)
        self.layout_frame_card_work.setSpacing(0)
        self.layout_frame_card_work.setObjectName(u"layout_frame_card_work")
        self.layout_frame_card_work.setContentsMargins(0, 0, 0, 0)
        self.card_header_work_types = QFrame(self.frame_card_work)
        self.card_header_work_types.setObjectName(u"card_header_work_types")
        self.hboxLayout1 = QHBoxLayout(self.card_header_work_types)
        self.hboxLayout1.setObjectName(u"hboxLayout1")
        self.hboxLayout1.setContentsMargins(20, -1, -1, -1)
        self.lbl_work_types_title = QLabel(self.card_header_work_types)
        self.lbl_work_types_title.setObjectName(u"lbl_work_types_title")

        self.hboxLayout1.addWidget(self.lbl_work_types_title)

        self.spacerItem2 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout1.addItem(self.spacerItem2)


        self.layout_frame_card_work.addWidget(self.card_header_work_types)

        self.frame_work_body = QFrame(self.frame_card_work)
        self.frame_work_body.setObjectName(u"frame_work_body")
        self.frame_work_body.setStyleSheet(u"QFrame#frame_work_body { border-radius:14px; }")
        self.grid_work_types = QGridLayout(self.frame_work_body)
        self.grid_work_types.setObjectName(u"grid_work_types")
        self.grid_work_types.setHorizontalSpacing(10)
        self.grid_work_types.setVerticalSpacing(5)
        self.grid_work_types.setContentsMargins(20, 16, 16, 16)
        self.chk_demolition = QCheckBox(self.frame_work_body)
        self.chk_demolition.setObjectName(u"chk_demolition")
        self.chk_demolition.setMinimumSize(QSize(0, 20))
        self.chk_demolition.setMaximumSize(QSize(24, 24))
        self.chk_demolition.setChecked(False)

        self.grid_work_types.addWidget(self.chk_demolition, 0, 7, 1, 1)

        self.lbl_demolition = QLabel(self.frame_work_body)
        self.lbl_demolition.setObjectName(u"lbl_demolition")

        self.grid_work_types.addWidget(self.lbl_demolition, 0, 0, 1, 7)

        self.cmb_demolition = QComboBox(self.frame_work_body)
        self.cmb_demolition.setObjectName(u"cmb_demolition")
        self.cmb_demolition.setMinimumSize(QSize(0, 46))
        self.cmb_demolition.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_demolition.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_demolition, 1, 0, 1, 2)

        self.dspn_demolition = QDoubleSpinBox(self.frame_work_body)
        self.dspn_demolition.setObjectName(u"dspn_demolition")
        self.dspn_demolition.setMinimumSize(QSize(100, 36))
        self.dspn_demolition.setMaximumSize(QSize(70, 36))
        self.dspn_demolition.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_demolition.setDecimals(0)
        self.dspn_demolition.setMinimum(0.000000000000000)
        self.dspn_demolition.setMaximum(9999.000000000000000)
        self.dspn_demolition.setSingleStep(1.000000000000000)
        self.dspn_demolition.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_demolition, 1, 2, 1, 1)

        self.lbl_unit_demolition = QLabel(self.frame_work_body)
        self.lbl_unit_demolition.setObjectName(u"lbl_unit_demolition")
        self.lbl_unit_demolition.setMinimumSize(QSize(0, 36))
        self.lbl_unit_demolition.setMaximumSize(QSize(60, 36))
        self.lbl_unit_demolition.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_demolition, 1, 3, 1, 1)

        self.cmb_demolition_2 = QComboBox(self.frame_work_body)
        self.cmb_demolition_2.setObjectName(u"cmb_demolition_2")
        self.cmb_demolition_2.setMinimumSize(QSize(0, 46))
        self.cmb_demolition_2.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_demolition_2.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_demolition_2, 1, 4, 1, 2)

        self.dspn_demolition_2 = QDoubleSpinBox(self.frame_work_body)
        self.dspn_demolition_2.setObjectName(u"dspn_demolition_2")
        self.dspn_demolition_2.setMinimumSize(QSize(100, 36))
        self.dspn_demolition_2.setMaximumSize(QSize(70, 36))
        self.dspn_demolition_2.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_demolition_2.setDecimals(0)
        self.dspn_demolition_2.setMinimum(0.000000000000000)
        self.dspn_demolition_2.setMaximum(9999.000000000000000)
        self.dspn_demolition_2.setSingleStep(1.000000000000000)
        self.dspn_demolition_2.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_demolition_2, 1, 6, 1, 1)

        self.lbl_unit_demolition_2 = QLabel(self.frame_work_body)
        self.lbl_unit_demolition_2.setObjectName(u"lbl_unit_demolition_2")
        self.lbl_unit_demolition_2.setMinimumSize(QSize(0, 36))
        self.lbl_unit_demolition_2.setMaximumSize(QSize(60, 36))
        self.lbl_unit_demolition_2.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_demolition_2, 1, 7, 1, 1)

        self.cmb_demolition_3 = QComboBox(self.frame_work_body)
        self.cmb_demolition_3.setObjectName(u"cmb_demolition_3")
        self.cmb_demolition_3.setMinimumSize(QSize(0, 46))
        self.cmb_demolition_3.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_demolition_3.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_demolition_3, 2, 0, 1, 2)

        self.dspn_demolition_3 = QDoubleSpinBox(self.frame_work_body)
        self.dspn_demolition_3.setObjectName(u"dspn_demolition_3")
        self.dspn_demolition_3.setMinimumSize(QSize(100, 36))
        self.dspn_demolition_3.setMaximumSize(QSize(70, 36))
        self.dspn_demolition_3.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_demolition_3.setDecimals(0)
        self.dspn_demolition_3.setMinimum(0.000000000000000)
        self.dspn_demolition_3.setMaximum(9999.000000000000000)
        self.dspn_demolition_3.setSingleStep(1.000000000000000)
        self.dspn_demolition_3.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_demolition_3, 2, 2, 1, 1)

        self.lbl_unit_demolition_3 = QLabel(self.frame_work_body)
        self.lbl_unit_demolition_3.setObjectName(u"lbl_unit_demolition_3")
        self.lbl_unit_demolition_3.setMinimumSize(QSize(0, 36))
        self.lbl_unit_demolition_3.setMaximumSize(QSize(60, 36))
        self.lbl_unit_demolition_3.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_demolition_3, 2, 3, 1, 1)

        self.cmb_demolition_4 = QComboBox(self.frame_work_body)
        self.cmb_demolition_4.setObjectName(u"cmb_demolition_4")
        self.cmb_demolition_4.setMinimumSize(QSize(0, 46))
        self.cmb_demolition_4.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_demolition_4.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_demolition_4, 2, 4, 1, 2)

        self.dspn_demolition_4 = QDoubleSpinBox(self.frame_work_body)
        self.dspn_demolition_4.setObjectName(u"dspn_demolition_4")
        self.dspn_demolition_4.setMinimumSize(QSize(100, 36))
        self.dspn_demolition_4.setMaximumSize(QSize(70, 36))
        self.dspn_demolition_4.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_demolition_4.setDecimals(0)
        self.dspn_demolition_4.setMinimum(0.000000000000000)
        self.dspn_demolition_4.setMaximum(9999.000000000000000)
        self.dspn_demolition_4.setSingleStep(1.000000000000000)
        self.dspn_demolition_4.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_demolition_4, 2, 6, 1, 1)

        self.lbl_unit_demolition_4 = QLabel(self.frame_work_body)
        self.lbl_unit_demolition_4.setObjectName(u"lbl_unit_demolition_4")
        self.lbl_unit_demolition_4.setMinimumSize(QSize(0, 36))
        self.lbl_unit_demolition_4.setMaximumSize(QSize(60, 36))
        self.lbl_unit_demolition_4.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_demolition_4, 2, 7, 1, 1)

        self.chk_preparation = QCheckBox(self.frame_work_body)
        self.chk_preparation.setObjectName(u"chk_preparation")
        self.chk_preparation.setMinimumSize(QSize(0, 20))
        self.chk_preparation.setMaximumSize(QSize(24, 24))
        self.chk_preparation.setChecked(False)

        self.grid_work_types.addWidget(self.chk_preparation, 3, 7, 1, 1)

        self.lbl_preparation = QLabel(self.frame_work_body)
        self.lbl_preparation.setObjectName(u"lbl_preparation")

        self.grid_work_types.addWidget(self.lbl_preparation, 3, 0, 1, 7)

        self.cmb_preparation = QComboBox(self.frame_work_body)
        self.cmb_preparation.setObjectName(u"cmb_preparation")
        self.cmb_preparation.setMinimumSize(QSize(0, 46))
        self.cmb_preparation.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_preparation.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_preparation, 4, 0, 1, 2)

        self.dspn_preparation = QDoubleSpinBox(self.frame_work_body)
        self.dspn_preparation.setObjectName(u"dspn_preparation")
        self.dspn_preparation.setMinimumSize(QSize(100, 36))
        self.dspn_preparation.setMaximumSize(QSize(70, 36))
        self.dspn_preparation.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_preparation.setDecimals(0)
        self.dspn_preparation.setMinimum(0.000000000000000)
        self.dspn_preparation.setMaximum(9999.000000000000000)
        self.dspn_preparation.setSingleStep(1.000000000000000)
        self.dspn_preparation.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_preparation, 4, 2, 1, 1)

        self.lbl_unit_preparation = QLabel(self.frame_work_body)
        self.lbl_unit_preparation.setObjectName(u"lbl_unit_preparation")
        self.lbl_unit_preparation.setMinimumSize(QSize(0, 36))
        self.lbl_unit_preparation.setMaximumSize(QSize(60, 36))
        self.lbl_unit_preparation.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_preparation, 4, 3, 1, 1)

        self.cmb_preparation_2 = QComboBox(self.frame_work_body)
        self.cmb_preparation_2.setObjectName(u"cmb_preparation_2")
        self.cmb_preparation_2.setMinimumSize(QSize(0, 46))
        self.cmb_preparation_2.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_preparation_2.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_preparation_2, 4, 4, 1, 2)

        self.dspn_preparation_2 = QDoubleSpinBox(self.frame_work_body)
        self.dspn_preparation_2.setObjectName(u"dspn_preparation_2")
        self.dspn_preparation_2.setMinimumSize(QSize(100, 36))
        self.dspn_preparation_2.setMaximumSize(QSize(70, 36))
        self.dspn_preparation_2.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_preparation_2.setDecimals(0)
        self.dspn_preparation_2.setMinimum(0.000000000000000)
        self.dspn_preparation_2.setMaximum(9999.000000000000000)
        self.dspn_preparation_2.setSingleStep(1.000000000000000)
        self.dspn_preparation_2.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_preparation_2, 4, 6, 1, 1)

        self.lbl_unit_preparation_2 = QLabel(self.frame_work_body)
        self.lbl_unit_preparation_2.setObjectName(u"lbl_unit_preparation_2")
        self.lbl_unit_preparation_2.setMinimumSize(QSize(0, 36))
        self.lbl_unit_preparation_2.setMaximumSize(QSize(60, 36))
        self.lbl_unit_preparation_2.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_preparation_2, 4, 7, 1, 1)

        self.cmb_preparation_3 = QComboBox(self.frame_work_body)
        self.cmb_preparation_3.setObjectName(u"cmb_preparation_3")
        self.cmb_preparation_3.setMinimumSize(QSize(0, 46))
        self.cmb_preparation_3.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_preparation_3.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_preparation_3, 5, 0, 1, 2)

        self.dspn_preparation_3 = QDoubleSpinBox(self.frame_work_body)
        self.dspn_preparation_3.setObjectName(u"dspn_preparation_3")
        self.dspn_preparation_3.setMinimumSize(QSize(100, 36))
        self.dspn_preparation_3.setMaximumSize(QSize(70, 36))
        self.dspn_preparation_3.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_preparation_3.setDecimals(0)
        self.dspn_preparation_3.setMinimum(0.000000000000000)
        self.dspn_preparation_3.setMaximum(9999.000000000000000)
        self.dspn_preparation_3.setSingleStep(1.000000000000000)
        self.dspn_preparation_3.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_preparation_3, 5, 2, 1, 1)

        self.lbl_unit_preparation_3 = QLabel(self.frame_work_body)
        self.lbl_unit_preparation_3.setObjectName(u"lbl_unit_preparation_3")
        self.lbl_unit_preparation_3.setMinimumSize(QSize(0, 36))
        self.lbl_unit_preparation_3.setMaximumSize(QSize(60, 36))
        self.lbl_unit_preparation_3.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_preparation_3, 5, 3, 1, 1)

        self.cmb_preparation_4 = QComboBox(self.frame_work_body)
        self.cmb_preparation_4.setObjectName(u"cmb_preparation_4")
        self.cmb_preparation_4.setMinimumSize(QSize(0, 46))
        self.cmb_preparation_4.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_preparation_4.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_preparation_4, 5, 4, 1, 2)

        self.dspn_preparation_4 = QDoubleSpinBox(self.frame_work_body)
        self.dspn_preparation_4.setObjectName(u"dspn_preparation_4")
        self.dspn_preparation_4.setMinimumSize(QSize(100, 36))
        self.dspn_preparation_4.setMaximumSize(QSize(70, 36))
        self.dspn_preparation_4.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_preparation_4.setDecimals(0)
        self.dspn_preparation_4.setMinimum(0.000000000000000)
        self.dspn_preparation_4.setMaximum(9999.000000000000000)
        self.dspn_preparation_4.setSingleStep(1.000000000000000)
        self.dspn_preparation_4.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_preparation_4, 5, 6, 1, 1)

        self.lbl_unit_preparation_4 = QLabel(self.frame_work_body)
        self.lbl_unit_preparation_4.setObjectName(u"lbl_unit_preparation_4")
        self.lbl_unit_preparation_4.setMinimumSize(QSize(0, 36))
        self.lbl_unit_preparation_4.setMaximumSize(QSize(60, 36))
        self.lbl_unit_preparation_4.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_preparation_4, 5, 7, 1, 1)

        self.chk_installation = QCheckBox(self.frame_work_body)
        self.chk_installation.setObjectName(u"chk_installation")
        self.chk_installation.setMinimumSize(QSize(0, 20))
        self.chk_installation.setMaximumSize(QSize(24, 24))
        self.chk_installation.setChecked(False)

        self.grid_work_types.addWidget(self.chk_installation, 6, 7, 1, 1)

        self.lbl_installation = QLabel(self.frame_work_body)
        self.lbl_installation.setObjectName(u"lbl_installation")

        self.grid_work_types.addWidget(self.lbl_installation, 6, 0, 1, 7)

        self.cmb_installation = QComboBox(self.frame_work_body)
        self.cmb_installation.setObjectName(u"cmb_installation")
        self.cmb_installation.setMinimumSize(QSize(0, 46))
        self.cmb_installation.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_installation.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_installation, 7, 0, 1, 2)

        self.dspn_installation = QDoubleSpinBox(self.frame_work_body)
        self.dspn_installation.setObjectName(u"dspn_installation")
        self.dspn_installation.setMinimumSize(QSize(100, 36))
        self.dspn_installation.setMaximumSize(QSize(70, 36))
        self.dspn_installation.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_installation.setDecimals(0)
        self.dspn_installation.setMinimum(0.000000000000000)
        self.dspn_installation.setMaximum(9999.000000000000000)
        self.dspn_installation.setSingleStep(1.000000000000000)
        self.dspn_installation.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_installation, 7, 2, 1, 1)

        self.lbl_unit_installation = QLabel(self.frame_work_body)
        self.lbl_unit_installation.setObjectName(u"lbl_unit_installation")
        self.lbl_unit_installation.setMinimumSize(QSize(0, 36))
        self.lbl_unit_installation.setMaximumSize(QSize(60, 36))
        self.lbl_unit_installation.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_installation, 7, 3, 1, 1)

        self.cmb_installation_2 = QComboBox(self.frame_work_body)
        self.cmb_installation_2.setObjectName(u"cmb_installation_2")
        self.cmb_installation_2.setMinimumSize(QSize(0, 46))
        self.cmb_installation_2.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_installation_2.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_installation_2, 7, 4, 1, 2)

        self.dspn_installation_2 = QDoubleSpinBox(self.frame_work_body)
        self.dspn_installation_2.setObjectName(u"dspn_installation_2")
        self.dspn_installation_2.setMinimumSize(QSize(100, 36))
        self.dspn_installation_2.setMaximumSize(QSize(70, 36))
        self.dspn_installation_2.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_installation_2.setDecimals(0)
        self.dspn_installation_2.setMinimum(0.000000000000000)
        self.dspn_installation_2.setMaximum(9999.000000000000000)
        self.dspn_installation_2.setSingleStep(1.000000000000000)
        self.dspn_installation_2.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_installation_2, 7, 6, 1, 1)

        self.lbl_unit_installation_2 = QLabel(self.frame_work_body)
        self.lbl_unit_installation_2.setObjectName(u"lbl_unit_installation_2")
        self.lbl_unit_installation_2.setMinimumSize(QSize(0, 36))
        self.lbl_unit_installation_2.setMaximumSize(QSize(60, 36))
        self.lbl_unit_installation_2.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_installation_2, 7, 7, 1, 1)

        self.cmb_installation_3 = QComboBox(self.frame_work_body)
        self.cmb_installation_3.setObjectName(u"cmb_installation_3")
        self.cmb_installation_3.setMinimumSize(QSize(0, 46))
        self.cmb_installation_3.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_installation_3.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_installation_3, 8, 0, 1, 2)

        self.dspn_installation_3 = QDoubleSpinBox(self.frame_work_body)
        self.dspn_installation_3.setObjectName(u"dspn_installation_3")
        self.dspn_installation_3.setMinimumSize(QSize(100, 36))
        self.dspn_installation_3.setMaximumSize(QSize(70, 36))
        self.dspn_installation_3.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_installation_3.setDecimals(0)
        self.dspn_installation_3.setMinimum(0.000000000000000)
        self.dspn_installation_3.setMaximum(9999.000000000000000)
        self.dspn_installation_3.setSingleStep(1.000000000000000)
        self.dspn_installation_3.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_installation_3, 8, 2, 1, 1)

        self.lbl_unit_installation_3 = QLabel(self.frame_work_body)
        self.lbl_unit_installation_3.setObjectName(u"lbl_unit_installation_3")
        self.lbl_unit_installation_3.setMinimumSize(QSize(0, 36))
        self.lbl_unit_installation_3.setMaximumSize(QSize(60, 36))
        self.lbl_unit_installation_3.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_installation_3, 8, 3, 1, 1)

        self.cmb_installation_4 = QComboBox(self.frame_work_body)
        self.cmb_installation_4.setObjectName(u"cmb_installation_4")
        self.cmb_installation_4.setMinimumSize(QSize(0, 46))
        self.cmb_installation_4.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_installation_4.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_installation_4, 8, 4, 1, 2)

        self.dspn_installation_4 = QDoubleSpinBox(self.frame_work_body)
        self.dspn_installation_4.setObjectName(u"dspn_installation_4")
        self.dspn_installation_4.setMinimumSize(QSize(100, 36))
        self.dspn_installation_4.setMaximumSize(QSize(70, 36))
        self.dspn_installation_4.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_installation_4.setDecimals(0)
        self.dspn_installation_4.setMinimum(0.000000000000000)
        self.dspn_installation_4.setMaximum(9999.000000000000000)
        self.dspn_installation_4.setSingleStep(1.000000000000000)
        self.dspn_installation_4.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_installation_4, 8, 6, 1, 1)

        self.lbl_unit_installation_4 = QLabel(self.frame_work_body)
        self.lbl_unit_installation_4.setObjectName(u"lbl_unit_installation_4")
        self.lbl_unit_installation_4.setMinimumSize(QSize(0, 36))
        self.lbl_unit_installation_4.setMaximumSize(QSize(60, 36))
        self.lbl_unit_installation_4.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_installation_4, 8, 7, 1, 1)

        self.chk_others = QCheckBox(self.frame_work_body)
        self.chk_others.setObjectName(u"chk_others")
        self.chk_others.setMinimumSize(QSize(0, 20))
        self.chk_others.setMaximumSize(QSize(24, 24))
        self.chk_others.setChecked(False)

        self.grid_work_types.addWidget(self.chk_others, 9, 7, 1, 1)

        self.lbl_others = QLabel(self.frame_work_body)
        self.lbl_others.setObjectName(u"lbl_others")

        self.grid_work_types.addWidget(self.lbl_others, 9, 0, 1, 7)

        self.cmb_others = QComboBox(self.frame_work_body)
        self.cmb_others.setObjectName(u"cmb_others")
        self.cmb_others.setMinimumSize(QSize(0, 46))
        self.cmb_others.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_others.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_others, 10, 0, 1, 2)

        self.dspn_others = QDoubleSpinBox(self.frame_work_body)
        self.dspn_others.setObjectName(u"dspn_others")
        self.dspn_others.setMinimumSize(QSize(100, 36))
        self.dspn_others.setMaximumSize(QSize(70, 36))
        self.dspn_others.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_others.setDecimals(0)
        self.dspn_others.setMinimum(0.000000000000000)
        self.dspn_others.setMaximum(9999.000000000000000)
        self.dspn_others.setSingleStep(1.000000000000000)
        self.dspn_others.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_others, 10, 2, 1, 1)

        self.lbl_unit_others = QLabel(self.frame_work_body)
        self.lbl_unit_others.setObjectName(u"lbl_unit_others")
        self.lbl_unit_others.setMinimumSize(QSize(0, 36))
        self.lbl_unit_others.setMaximumSize(QSize(60, 36))
        self.lbl_unit_others.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_others, 10, 3, 1, 1)

        self.cmb_others_2 = QComboBox(self.frame_work_body)
        self.cmb_others_2.setObjectName(u"cmb_others_2")
        self.cmb_others_2.setMinimumSize(QSize(0, 46))
        self.cmb_others_2.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_others_2.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_others_2, 10, 4, 1, 2)

        self.dspn_others_2 = QDoubleSpinBox(self.frame_work_body)
        self.dspn_others_2.setObjectName(u"dspn_others_2")
        self.dspn_others_2.setMinimumSize(QSize(100, 36))
        self.dspn_others_2.setMaximumSize(QSize(70, 36))
        self.dspn_others_2.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_others_2.setDecimals(0)
        self.dspn_others_2.setMinimum(0.000000000000000)
        self.dspn_others_2.setMaximum(9999.000000000000000)
        self.dspn_others_2.setSingleStep(1.000000000000000)
        self.dspn_others_2.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_others_2, 10, 6, 1, 1)

        self.lbl_unit_others_2 = QLabel(self.frame_work_body)
        self.lbl_unit_others_2.setObjectName(u"lbl_unit_others_2")
        self.lbl_unit_others_2.setMinimumSize(QSize(0, 36))
        self.lbl_unit_others_2.setMaximumSize(QSize(60, 36))
        self.lbl_unit_others_2.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_others_2, 10, 7, 1, 1)

        self.chk_reparo = QCheckBox(self.frame_work_body)
        self.chk_reparo.setObjectName(u"chk_reparo")
        self.chk_reparo.setMinimumSize(QSize(0, 20))
        self.chk_reparo.setMaximumSize(QSize(24, 24))
        self.chk_reparo.setChecked(False)

        self.grid_work_types.addWidget(self.chk_reparo, 11, 7, 1, 1)

        self.lbl_reparo = QLabel(self.frame_work_body)
        self.lbl_reparo.setObjectName(u"lbl_reparo")

        self.grid_work_types.addWidget(self.lbl_reparo, 11, 0, 1, 7)

        self.cmb_reparo = QComboBox(self.frame_work_body)
        self.cmb_reparo.setObjectName(u"cmb_reparo")
        self.cmb_reparo.setMinimumSize(QSize(0, 46))
        self.cmb_reparo.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_reparo.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_reparo, 12, 0, 1, 2)

        self.dspn_reparo = QDoubleSpinBox(self.frame_work_body)
        self.dspn_reparo.setObjectName(u"dspn_reparo")
        self.dspn_reparo.setMinimumSize(QSize(100, 36))
        self.dspn_reparo.setMaximumSize(QSize(70, 36))
        self.dspn_reparo.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_reparo.setDecimals(0)
        self.dspn_reparo.setMinimum(0.000000000000000)
        self.dspn_reparo.setMaximum(9999.000000000000000)
        self.dspn_reparo.setSingleStep(1.000000000000000)
        self.dspn_reparo.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_reparo, 12, 2, 1, 1)

        self.lbl_unit_reparo = QLabel(self.frame_work_body)
        self.lbl_unit_reparo.setObjectName(u"lbl_unit_reparo")
        self.lbl_unit_reparo.setMinimumSize(QSize(0, 36))
        self.lbl_unit_reparo.setMaximumSize(QSize(60, 36))
        self.lbl_unit_reparo.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_reparo, 12, 3, 1, 1)

        self.cmb_reparo_2 = QComboBox(self.frame_work_body)
        self.cmb_reparo_2.setObjectName(u"cmb_reparo_2")
        self.cmb_reparo_2.setMinimumSize(QSize(0, 46))
        self.cmb_reparo_2.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_reparo_2.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.cmb_reparo_2, 12, 4, 1, 2)

        self.dspn_reparo_2 = QDoubleSpinBox(self.frame_work_body)
        self.dspn_reparo_2.setObjectName(u"dspn_reparo_2")
        self.dspn_reparo_2.setMinimumSize(QSize(100, 36))
        self.dspn_reparo_2.setMaximumSize(QSize(70, 36))
        self.dspn_reparo_2.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.dspn_reparo_2.setDecimals(0)
        self.dspn_reparo_2.setMinimum(0.000000000000000)
        self.dspn_reparo_2.setMaximum(9999.000000000000000)
        self.dspn_reparo_2.setSingleStep(1.000000000000000)
        self.dspn_reparo_2.setValue(1.000000000000000)

        self.grid_work_types.addWidget(self.dspn_reparo_2, 12, 6, 1, 1)

        self.lbl_unit_reparo_2 = QLabel(self.frame_work_body)
        self.lbl_unit_reparo_2.setObjectName(u"lbl_unit_reparo_2")
        self.lbl_unit_reparo_2.setMinimumSize(QSize(0, 36))
        self.lbl_unit_reparo_2.setMaximumSize(QSize(60, 36))
        self.lbl_unit_reparo_2.setAlignment(Qt.AlignCenter)

        self.grid_work_types.addWidget(self.lbl_unit_reparo_2, 12, 7, 1, 1)

        self.lbl_note = QLabel(self.frame_work_body)
        self.lbl_note.setObjectName(u"lbl_note")

        self.grid_work_types.addWidget(self.lbl_note, 13, 0, 1, 8)

        self.txt_note = QTextEdit(self.frame_work_body)
        self.txt_note.setObjectName(u"txt_note")
        self.txt_note.setMinimumSize(QSize(0, 70))
        self.txt_note.setMaximumSize(QSize(16777215, 90))
        self.txt_note.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_work_types.addWidget(self.txt_note, 14, 0, 1, 8)

        self.txt_job_id = QLineEdit(self.frame_work_body)
        self.txt_job_id.setObjectName(u"txt_job_id")
        self.txt_job_id.setMinimumSize(QSize(0, 36))
        self.txt_job_id.setMaximumSize(QSize(16777215, 36))
        self.txt_job_id.setVisible(False)
        self.txt_job_id.setReadOnly(True)

        self.grid_work_types.addWidget(self.txt_job_id, 15, 0, 1, 1)


        self.layout_frame_card_work.addWidget(self.frame_work_body)


        self.layout_col_work_types.addWidget(self.frame_card_work)


        self.layout_work_client_row.addLayout(self.layout_col_work_types)


        self.layout_job_body_cards.addLayout(self.layout_work_client_row)

        self.scroll_job_form.setWidget(self.frame_job_body)

        self.layout_job_card.addWidget(self.scroll_job_form)

        self.frame_job_footer = QFrame(self.frame_job_card)
        self.frame_job_footer.setObjectName(u"frame_job_footer")
        self.frame_job_footer.setMinimumSize(QSize(100, 0))
        self.hboxLayout2 = QHBoxLayout(self.frame_job_footer)
        self.hboxLayout2.setObjectName(u"hboxLayout2")
        self.hboxLayout2.setContentsMargins(20, 12, 20, 12)
        self.spacerItem3 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout2.addItem(self.spacerItem3)

        self.btn_delete_job = QPushButton(self.frame_job_footer)
        self.btn_delete_job.setObjectName(u"btn_delete_job")
        self.btn_delete_job.setMinimumSize(QSize(90, 36))
        self.btn_delete_job.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout2.addWidget(self.btn_delete_job)

        self.btn_save_job = QPushButton(self.frame_job_footer)
        self.btn_save_job.setObjectName(u"btn_save_job")
        self.btn_save_job.setMinimumSize(QSize(110, 36))
        self.btn_save_job.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout2.addWidget(self.btn_save_job)


        self.layout_job_card.addWidget(self.frame_job_footer)


        self.layout_jobs_right_panel.addWidget(self.frame_job_card)


        self.layout_tab_jobs_master.addWidget(self.frame_jobs_right_panel)

        self.frame_client_drawer = QFrame(self.tab_jobs_master)
        self.frame_client_drawer.setObjectName(u"frame_client_drawer")
        self.frame_client_drawer.setMinimumSize(QSize(0, 0))
        self.frame_client_drawer.setMaximumSize(QSize(0, 16777215))
        self.frame_client_drawer.setStyleSheet(u"QFrame#frame_client_drawer { background-color: #FFFFFF; border-left: 1px solid #E1E8F0; }")
        self.layout_client_drawer = QVBoxLayout(self.frame_client_drawer)
        self.layout_client_drawer.setSpacing(0)
        self.layout_client_drawer.setObjectName(u"layout_client_drawer")
        self.layout_client_drawer.setContentsMargins(16, 0, 0, 0)
        self.scroll_client_drawer = QScrollArea(self.frame_client_drawer)
        self.scroll_client_drawer.setObjectName(u"scroll_client_drawer")
        self.scroll_client_drawer.setFrameShape(QFrame.NoFrame)
        self.scroll_client_drawer.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_client_drawer.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_client_drawer.setWidgetResizable(True)
        self.scroll_client_drawer_contents = QWidget()
        self.scroll_client_drawer_contents.setObjectName(u"scroll_client_drawer_contents")
        self.scroll_client_drawer_contents.setGeometry(QRect(0, 0, 318, 907))
        self.layout_scroll_client_drawer_contents = QVBoxLayout(self.scroll_client_drawer_contents)
        self.layout_scroll_client_drawer_contents.setObjectName(u"layout_scroll_client_drawer_contents")
        self.layout_scroll_client_drawer_contents.setContentsMargins(0, 0, 4, 0)
        self.layout_col_client_and_extra = QVBoxLayout()
        self.layout_col_client_and_extra.setSpacing(16)
        self.layout_col_client_and_extra.setObjectName(u"layout_col_client_and_extra")
        self.layout_col_client_and_extra.setContentsMargins(0, 0, 0, 0)
        self.frame_card_client = QFrame(self.scroll_client_drawer_contents)
        self.frame_card_client.setObjectName(u"frame_card_client")
        self.layout_frame_card_client = QVBoxLayout(self.frame_card_client)
        self.layout_frame_card_client.setSpacing(0)
        self.layout_frame_card_client.setObjectName(u"layout_frame_card_client")
        self.layout_frame_card_client.setContentsMargins(0, 0, 0, 0)
        self.card_header_client_info = QFrame(self.frame_card_client)
        self.card_header_client_info.setObjectName(u"card_header_client_info")
        self.hboxLayout3 = QHBoxLayout(self.card_header_client_info)
        self.hboxLayout3.setObjectName(u"hboxLayout3")
        self.hboxLayout3.setContentsMargins(20, -1, -1, -1)
        self.lbl_client_info_title = QLabel(self.card_header_client_info)
        self.lbl_client_info_title.setObjectName(u"lbl_client_info_title")

        self.hboxLayout3.addWidget(self.lbl_client_info_title)

        self.spacerItem4 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout3.addItem(self.spacerItem4)


        self.layout_frame_card_client.addWidget(self.card_header_client_info)

        self.frame_client_body = QFrame(self.frame_card_client)
        self.frame_client_body.setObjectName(u"frame_client_body")
        self.frame_client_body.setGeometry(QRect(0, 0, 373, 314))
        self.grid_client_info = QGridLayout(self.frame_client_body)
        self.grid_client_info.setObjectName(u"grid_client_info")
        self.grid_client_info.setHorizontalSpacing(12)
        self.grid_client_info.setVerticalSpacing(8)
        self.grid_client_info.setContentsMargins(20, 16, 20, 16)
        self.lbl_job_address = QLabel(self.frame_client_body)
        self.lbl_job_address.setObjectName(u"lbl_job_address")

        self.grid_client_info.addWidget(self.lbl_job_address, 0, 0, 1, 3)

        self.lbl_job_address2 = QLabel(self.frame_client_body)
        self.lbl_job_address2.setObjectName(u"lbl_job_address2")
        self.lbl_job_address2.setWordWrap(True)

        self.grid_client_info.addWidget(self.lbl_job_address2, 0, 3, 1, 3)

        self.cmb_client_address = QComboBox(self.frame_client_body)
        self.cmb_client_address.setObjectName(u"cmb_client_address")
        self.cmb_client_address.setMinimumSize(QSize(0, 46))
        self.cmb_client_address.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_client_address.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")
        self.cmb_client_address.setEditable(True)
        self.cmb_client_address.setInsertPolicy(QComboBox.InsertAtTop)

        self.grid_client_info.addWidget(self.cmb_client_address, 1, 0, 1, 3)

        self.txt_client_address2 = QLineEdit(self.frame_client_body)
        self.txt_client_address2.setObjectName(u"txt_client_address2")
        self.txt_client_address2.setMinimumSize(QSize(0, 36))
        self.txt_client_address2.setMaximumSize(QSize(16777215, 36))
        self.txt_client_address2.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_client_info.addWidget(self.txt_client_address2, 1, 3, 1, 3)

        self.lbl_state = QLabel(self.frame_client_body)
        self.lbl_state.setObjectName(u"lbl_state")

        self.grid_client_info.addWidget(self.lbl_state, 2, 0, 1, 2)

        self.lbl_city = QLabel(self.frame_client_body)
        self.lbl_city.setObjectName(u"lbl_city")

        self.grid_client_info.addWidget(self.lbl_city, 2, 2, 1, 2)

        self.lbl_zip = QLabel(self.frame_client_body)
        self.lbl_zip.setObjectName(u"lbl_zip")

        self.grid_client_info.addWidget(self.lbl_zip, 2, 4, 1, 2)

        self.cmb_client_state = QComboBox(self.frame_client_body)
        self.cmb_client_state.setObjectName(u"cmb_client_state")
        self.cmb_client_state.setMinimumSize(QSize(0, 46))
        self.cmb_client_state.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_client_state.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_client_info.addWidget(self.cmb_client_state, 3, 0, 1, 2)

        self.cmb_client_city = QComboBox(self.frame_client_body)
        self.cmb_client_city.setObjectName(u"cmb_client_city")
        self.cmb_client_city.setMinimumSize(QSize(0, 46))
        self.cmb_client_city.setMaximumSize(QSize(16777215, 16777215))
        self.cmb_client_city.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_client_info.addWidget(self.cmb_client_city, 3, 2, 1, 2)

        self.txt_client_zip = QLineEdit(self.frame_client_body)
        self.txt_client_zip.setObjectName(u"txt_client_zip")
        self.txt_client_zip.setMinimumSize(QSize(0, 36))
        self.txt_client_zip.setMaximumSize(QSize(110, 36))
        self.txt_client_zip.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_client_info.addWidget(self.txt_client_zip, 3, 4, 1, 2)

        self.lbl_client = QLabel(self.frame_client_body)
        self.lbl_client.setObjectName(u"lbl_client")

        self.grid_client_info.addWidget(self.lbl_client, 4, 0, 1, 3)

        self.lbl_phone = QLabel(self.frame_client_body)
        self.lbl_phone.setObjectName(u"lbl_phone")

        self.grid_client_info.addWidget(self.lbl_phone, 4, 3, 1, 3)

        self.txt_client_name = QLineEdit(self.frame_client_body)
        self.txt_client_name.setObjectName(u"txt_client_name")
        self.txt_client_name.setMinimumSize(QSize(0, 46))
        self.txt_client_name.setMaximumSize(QSize(16777215, 16777215))
        self.txt_client_name.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_client_info.addWidget(self.txt_client_name, 5, 0, 1, 3)

        self.txt_client_phone = QLineEdit(self.frame_client_body)
        self.txt_client_phone.setObjectName(u"txt_client_phone")
        self.txt_client_phone.setMinimumSize(QSize(0, 36))
        self.txt_client_phone.setMaximumSize(QSize(160, 36))
        self.txt_client_phone.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_client_info.addWidget(self.txt_client_phone, 5, 3, 1, 3)

        self.lbl_client_email = QLabel(self.frame_client_body)
        self.lbl_client_email.setObjectName(u"lbl_client_email")

        self.grid_client_info.addWidget(self.lbl_client_email, 6, 0, 1, 3)

        self.lbl_phone_2 = QLabel(self.frame_client_body)
        self.lbl_phone_2.setObjectName(u"lbl_phone_2")

        self.grid_client_info.addWidget(self.lbl_phone_2, 6, 3, 1, 3)

        self.txt_client_email = QLineEdit(self.frame_client_body)
        self.txt_client_email.setObjectName(u"txt_client_email")
        self.txt_client_email.setMinimumSize(QSize(0, 36))
        self.txt_client_email.setMaximumSize(QSize(16777215, 36))
        self.txt_client_email.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_client_info.addWidget(self.txt_client_email, 7, 0, 1, 3)

        self.txt_client_phone_2 = QLineEdit(self.frame_client_body)
        self.txt_client_phone_2.setObjectName(u"txt_client_phone_2")
        self.txt_client_phone_2.setMinimumSize(QSize(0, 36))
        self.txt_client_phone_2.setMaximumSize(QSize(160, 36))
        self.txt_client_phone_2.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")

        self.grid_client_info.addWidget(self.txt_client_phone_2, 7, 3, 1, 3)


        self.layout_frame_card_client.addWidget(self.frame_client_body)


        self.layout_col_client_and_extra.addWidget(self.frame_card_client)

        self.frame_card_materials = QFrame(self.scroll_client_drawer_contents)
        self.frame_card_materials.setObjectName(u"frame_card_materials")
        self.layout_frame_card_materials = QVBoxLayout(self.frame_card_materials)
        self.layout_frame_card_materials.setSpacing(0)
        self.layout_frame_card_materials.setObjectName(u"layout_frame_card_materials")
        self.layout_frame_card_materials.setContentsMargins(0, 0, 0, 0)
        self.card_header_materials = QFrame(self.frame_card_materials)
        self.card_header_materials.setObjectName(u"card_header_materials")
        self.hboxLayout4 = QHBoxLayout(self.card_header_materials)
        self.hboxLayout4.setObjectName(u"hboxLayout4")
        self.hboxLayout4.setContentsMargins(20, -1, -1, -1)
        self.lbl_materials_title = QLabel(self.card_header_materials)
        self.lbl_materials_title.setObjectName(u"lbl_materials_title")

        self.hboxLayout4.addWidget(self.lbl_materials_title)

        self.spacerItem5 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout4.addItem(self.spacerItem5)


        self.layout_frame_card_materials.addWidget(self.card_header_materials)

        self.frame_materials_body = QFrame(self.frame_card_materials)
        self.frame_materials_body.setObjectName(u"frame_materials_body")
        self.frame_materials_body.setStyleSheet(u"QFrame#frame_materials_body { border-radius:14px; }")
        self.layout_materials_body = QVBoxLayout(self.frame_materials_body)
        self.layout_materials_body.setSpacing(10)
        self.layout_materials_body.setObjectName(u"layout_materials_body")
        self.layout_materials_body.setContentsMargins(20, 16, 20, 16)
        self.table_job_materials = QTableWidget(self.frame_materials_body)
        if (self.table_job_materials.columnCount() < 3):
            self.table_job_materials.setColumnCount(3)
        __qtablewidgetitem21 = QTableWidgetItem()
        self.table_job_materials.setHorizontalHeaderItem(0, __qtablewidgetitem21)
        __qtablewidgetitem22 = QTableWidgetItem()
        self.table_job_materials.setHorizontalHeaderItem(1, __qtablewidgetitem22)
        __qtablewidgetitem23 = QTableWidgetItem()
        self.table_job_materials.setHorizontalHeaderItem(2, __qtablewidgetitem23)
        self.table_job_materials.setObjectName(u"table_job_materials")
        self.table_job_materials.setMinimumSize(QSize(0, 133))
        self.table_job_materials.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_job_materials.setAlternatingRowColors(True)
        self.table_job_materials.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_job_materials.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_job_materials.setColumnCount(3)
        self.table_job_materials.horizontalHeader().setStretchLastSection(True)

        self.layout_materials_body.addWidget(self.table_job_materials)

        self.layout_add_material_row = QHBoxLayout()
        self.layout_add_material_row.setSpacing(8)
        self.layout_add_material_row.setObjectName(u"layout_add_material_row")
        self.cmb_material_product = QComboBox(self.frame_materials_body)
        self.cmb_material_product.setObjectName(u"cmb_material_product")
        self.cmb_material_product.setMinimumSize(QSize(0, 46))

        self.layout_add_material_row.addWidget(self.cmb_material_product)

        self.dspn_material_qty = QDoubleSpinBox(self.frame_materials_body)
        self.dspn_material_qty.setObjectName(u"dspn_material_qty")
        self.dspn_material_qty.setMinimumSize(QSize(90, 40))
        self.dspn_material_qty.setDecimals(2)
        self.dspn_material_qty.setMaximum(99999.990000000005239)
        self.dspn_material_qty.setValue(1.000000000000000)

        self.layout_add_material_row.addWidget(self.dspn_material_qty)

        self.btn_add_material = QPushButton(self.frame_materials_body)
        self.btn_add_material.setObjectName(u"btn_add_material")
        self.btn_add_material.setMinimumSize(QSize(0, 40))
        self.btn_add_material.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_add_material_row.addWidget(self.btn_add_material)


        self.layout_materials_body.addLayout(self.layout_add_material_row)

        self.btn_remove_material = QPushButton(self.frame_materials_body)
        self.btn_remove_material.setObjectName(u"btn_remove_material")
        self.btn_remove_material.setMinimumSize(QSize(0, 32))
        self.btn_remove_material.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_materials_body.addWidget(self.btn_remove_material)

        self.lbl_materials_total_cost = QLabel(self.frame_materials_body)
        self.lbl_materials_total_cost.setObjectName(u"lbl_materials_total_cost")
        self.lbl_materials_total_cost.setVisible(False)
        self.lbl_materials_total_cost.setStyleSheet(u"font-size:13px; font-weight:700; color:#1565C0; background:transparent;")

        self.layout_materials_body.addWidget(self.lbl_materials_total_cost)


        self.layout_frame_card_materials.addWidget(self.frame_materials_body)


        self.layout_col_client_and_extra.addWidget(self.frame_card_materials)


        self.layout_scroll_client_drawer_contents.addLayout(self.layout_col_client_and_extra)

        self.spacerItem6 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_scroll_client_drawer_contents.addItem(self.spacerItem6)

        self.scroll_client_drawer.setWidget(self.scroll_client_drawer_contents)

        self.layout_client_drawer.addWidget(self.scroll_client_drawer)


        self.layout_tab_jobs_master.addWidget(self.frame_client_drawer)

        self.tabWidget_jobs.addTab(self.tab_jobs_master, "")
        self.tab_schedule = QWidget()
        self.tab_schedule.setObjectName(u"tab_schedule")
        self.layout_tab_schedule = QHBoxLayout(self.tab_schedule)
        self.layout_tab_schedule.setSpacing(16)
        self.layout_tab_schedule.setObjectName(u"layout_tab_schedule")
        self.layout_tab_schedule.setContentsMargins(20, 20, 20, 20)
        self.calendar_schedule = QCalendarWidget(self.tab_schedule)
        self.calendar_schedule.setObjectName(u"calendar_schedule")
        self.calendar_schedule.setMinimumSize(QSize(440, 400))
        self.calendar_schedule.setGridVisible(True)

        self.layout_tab_schedule.addWidget(self.calendar_schedule)

        self.layout_schedule_side = QVBoxLayout()
        self.layout_schedule_side.setObjectName(u"layout_schedule_side")
        self.lbl_schedule_selected_date = QLabel(self.tab_schedule)
        self.lbl_schedule_selected_date.setObjectName(u"lbl_schedule_selected_date")

        self.layout_schedule_side.addWidget(self.lbl_schedule_selected_date)

        self.list_schedule_jobs = QListWidget(self.tab_schedule)
        self.list_schedule_jobs.setObjectName(u"list_schedule_jobs")
        self.list_schedule_jobs.setMinimumSize(QSize(300, 0))

        self.layout_schedule_side.addWidget(self.list_schedule_jobs)

        self.btn_schedule_new_job = QPushButton(self.tab_schedule)
        self.btn_schedule_new_job.setObjectName(u"btn_schedule_new_job")
        self.btn_schedule_new_job.setMinimumSize(QSize(0, 42))
        self.btn_schedule_new_job.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_schedule_side.addWidget(self.btn_schedule_new_job)


        self.layout_tab_schedule.addLayout(self.layout_schedule_side)

        self.tabWidget_jobs.addTab(self.tab_schedule, "")

        self.layout_jobs.addWidget(self.tabWidget_jobs)

        self.Pages.addWidget(self.pg_jobs)
        self.pg_companies = QWidget()
        self.pg_companies.setObjectName(u"pg_companies")
        self.layout_companies_page = QVBoxLayout(self.pg_companies)
        self.layout_companies_page.setSpacing(0)
        self.layout_companies_page.setObjectName(u"layout_companies_page")
        self.layout_companies_page.setContentsMargins(0, 0, 0, 0)
        self.tabWidget_companies_page = QTabWidget(self.pg_companies)
        self.tabWidget_companies_page.setObjectName(u"tabWidget_companies_page")
        self.tab_companies_master = QWidget()
        self.tab_companies_master.setObjectName(u"tab_companies_master")
        self.layout_tab_companies_master = QHBoxLayout(self.tab_companies_master)
        self.layout_tab_companies_master.setSpacing(16)
        self.layout_tab_companies_master.setObjectName(u"layout_tab_companies_master")
        self.layout_tab_companies_master.setContentsMargins(16, 16, 16, 16)
        self.layout_companies_left_panel = QVBoxLayout()
        self.layout_companies_left_panel.setSpacing(10)
        self.layout_companies_left_panel.setObjectName(u"layout_companies_left_panel")
        self.layout_companies_left_panel.setContentsMargins(0, 0, 0, 0)
        self.layout_companies_row_search = QHBoxLayout()
        self.layout_companies_row_search.setSpacing(8)
        self.layout_companies_row_search.setObjectName(u"layout_companies_row_search")
        self.txt_search_companies = QLineEdit(self.tab_companies_master)
        self.txt_search_companies.setObjectName(u"txt_search_companies")
        self.txt_search_companies.setMinimumSize(QSize(280, 36))

        self.layout_companies_row_search.addWidget(self.txt_search_companies)


        self.layout_companies_left_panel.addLayout(self.layout_companies_row_search)

        self.layout_companies_row_filters = QHBoxLayout()
        self.layout_companies_row_filters.setSpacing(8)
        self.layout_companies_row_filters.setObjectName(u"layout_companies_row_filters")
        self.cmb_filter_company_status = QComboBox(self.tab_companies_master)
        self.cmb_filter_company_status.addItem("")
        self.cmb_filter_company_status.addItem("")
        self.cmb_filter_company_status.addItem("")
        self.cmb_filter_company_status.setObjectName(u"cmb_filter_company_status")
        self.cmb_filter_company_status.setMinimumSize(QSize(140, 46))
        self.cmb_filter_company_status.setMaximumSize(QSize(16777215, 16777215))

        self.layout_companies_row_filters.addWidget(self.cmb_filter_company_status)

        self.btn_refresh_companies = QPushButton(self.tab_companies_master)
        self.btn_refresh_companies.setObjectName(u"btn_refresh_companies")
        self.btn_refresh_companies.setMinimumSize(QSize(90, 36))
        self.btn_refresh_companies.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_companies_row_filters.addWidget(self.btn_refresh_companies)


        self.layout_companies_left_panel.addLayout(self.layout_companies_row_filters)

        self.layout_companies_row_export = QHBoxLayout()
        self.layout_companies_row_export.setSpacing(8)
        self.layout_companies_row_export.setObjectName(u"layout_companies_row_export")
        self.btn_export_excel_companies = QPushButton(self.tab_companies_master)
        self.btn_export_excel_companies.setObjectName(u"btn_export_excel_companies")
        self.btn_export_excel_companies.setMinimumSize(QSize(110, 36))
        self.btn_export_excel_companies.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_companies_row_export.addWidget(self.btn_export_excel_companies)

        self.btn_export_pdf_companies = QPushButton(self.tab_companies_master)
        self.btn_export_pdf_companies.setObjectName(u"btn_export_pdf_companies")
        self.btn_export_pdf_companies.setMinimumSize(QSize(100, 36))
        self.btn_export_pdf_companies.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_companies_row_export.addWidget(self.btn_export_pdf_companies)


        self.layout_companies_left_panel.addLayout(self.layout_companies_row_export)

        self.layout_companies_row_actions = QHBoxLayout()
        self.layout_companies_row_actions.setSpacing(8)
        self.layout_companies_row_actions.setObjectName(u"layout_companies_row_actions")
        self.btn_new_company = QPushButton(self.tab_companies_master)
        self.btn_new_company.setObjectName(u"btn_new_company")
        self.btn_new_company.setMinimumSize(QSize(130, 36))
        self.btn_new_company.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_companies_row_actions.addWidget(self.btn_new_company)


        self.layout_companies_left_panel.addLayout(self.layout_companies_row_actions)

        self.btn_toggle_companies_table_expanded = QPushButton(self.tab_companies_master)
        self.btn_toggle_companies_table_expanded.setObjectName(u"btn_toggle_companies_table_expanded")
        self.btn_toggle_companies_table_expanded.setMinimumSize(QSize(0, 34))
        self.btn_toggle_companies_table_expanded.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle_companies_table_expanded.setStyleSheet(u"QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; border-radius: 6px; font-size: 12px; font-weight: 600; } QPushButton:hover { background-color: #E1E8F0; }")

        self.layout_companies_left_panel.addWidget(self.btn_toggle_companies_table_expanded)

        self.table_companies = QTableWidget(self.tab_companies_master)
        if (self.table_companies.columnCount() < 12):
            self.table_companies.setColumnCount(12)
        __qtablewidgetitem24 = QTableWidgetItem()
        self.table_companies.setHorizontalHeaderItem(0, __qtablewidgetitem24)
        __qtablewidgetitem25 = QTableWidgetItem()
        self.table_companies.setHorizontalHeaderItem(1, __qtablewidgetitem25)
        __qtablewidgetitem26 = QTableWidgetItem()
        self.table_companies.setHorizontalHeaderItem(2, __qtablewidgetitem26)
        __qtablewidgetitem27 = QTableWidgetItem()
        self.table_companies.setHorizontalHeaderItem(3, __qtablewidgetitem27)
        __qtablewidgetitem28 = QTableWidgetItem()
        self.table_companies.setHorizontalHeaderItem(4, __qtablewidgetitem28)
        __qtablewidgetitem29 = QTableWidgetItem()
        self.table_companies.setHorizontalHeaderItem(5, __qtablewidgetitem29)
        __qtablewidgetitem30 = QTableWidgetItem()
        self.table_companies.setHorizontalHeaderItem(6, __qtablewidgetitem30)
        __qtablewidgetitem31 = QTableWidgetItem()
        self.table_companies.setHorizontalHeaderItem(7, __qtablewidgetitem31)
        __qtablewidgetitem32 = QTableWidgetItem()
        self.table_companies.setHorizontalHeaderItem(8, __qtablewidgetitem32)
        __qtablewidgetitem33 = QTableWidgetItem()
        self.table_companies.setHorizontalHeaderItem(9, __qtablewidgetitem33)
        __qtablewidgetitem34 = QTableWidgetItem()
        self.table_companies.setHorizontalHeaderItem(10, __qtablewidgetitem34)
        __qtablewidgetitem35 = QTableWidgetItem()
        self.table_companies.setHorizontalHeaderItem(11, __qtablewidgetitem35)
        self.table_companies.setObjectName(u"table_companies")
        self.table_companies.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_companies.setAlternatingRowColors(True)
        self.table_companies.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_companies.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_companies.setSortingEnabled(True)
        self.table_companies.setColumnCount(12)
        self.table_companies.horizontalHeader().setStretchLastSection(True)

        self.layout_companies_left_panel.addWidget(self.table_companies)


        self.layout_tab_companies_master.addLayout(self.layout_companies_left_panel)

        self.layout_companies_right_panel = QVBoxLayout()
        self.layout_companies_right_panel.setSpacing(0)
        self.layout_companies_right_panel.setObjectName(u"layout_companies_right_panel")
        self.layout_companies_right_panel.setContentsMargins(0, 0, 0, 0)
        self.frame_company_card = QFrame(self.tab_companies_master)
        self.frame_company_card.setObjectName(u"frame_company_card")
        self.frame_company_card.setMaximumSize(QSize(860, 16777215))
        self.layout_company_card = QVBoxLayout(self.frame_company_card)
        self.layout_company_card.setSpacing(0)
        self.layout_company_card.setObjectName(u"layout_company_card")
        self.layout_company_card.setContentsMargins(0, 0, 0, 0)
        self.card_header_company = QFrame(self.frame_company_card)
        self.card_header_company.setObjectName(u"card_header_company")
        self.hboxLayout5 = QHBoxLayout(self.card_header_company)
        self.hboxLayout5.setObjectName(u"hboxLayout5")
        self.hboxLayout5.setContentsMargins(20, -1, -1, -1)
        self.lbl_company_form_title = QLabel(self.card_header_company)
        self.lbl_company_form_title.setObjectName(u"lbl_company_form_title")

        self.hboxLayout5.addWidget(self.lbl_company_form_title)

        self.spacerItem7 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout5.addItem(self.spacerItem7)

        self.lbl_company_id_display = QLabel(self.card_header_company)
        self.lbl_company_id_display.setObjectName(u"lbl_company_id_display")

        self.hboxLayout5.addWidget(self.lbl_company_id_display)


        self.layout_company_card.addWidget(self.card_header_company)

        self.scroll_company_form = QScrollArea(self.frame_company_card)
        self.scroll_company_form.setObjectName(u"scroll_company_form")
        self.scroll_company_form.setFrameShape(QFrame.NoFrame)
        self.scroll_company_form.setWidgetResizable(True)
        self.scrollContents_company = QWidget()
        self.scrollContents_company.setObjectName(u"scrollContents_company")
        self.scrollContents_company.setGeometry(QRect(0, 0, 852, 599))
        self.grid_company_form = QGridLayout(self.scrollContents_company)
        self.grid_company_form.setObjectName(u"grid_company_form")
        self.grid_company_form.setHorizontalSpacing(16)
        self.grid_company_form.setVerticalSpacing(10)
        self.grid_company_form.setContentsMargins(20, 16, 20, 16)
        self.lbl_company_name = QLabel(self.scrollContents_company)
        self.lbl_company_name.setObjectName(u"lbl_company_name")

        self.grid_company_form.addWidget(self.lbl_company_name, 0, 0, 1, 2)

        self.lbl_contact_name = QLabel(self.scrollContents_company)
        self.lbl_contact_name.setObjectName(u"lbl_contact_name")

        self.grid_company_form.addWidget(self.lbl_contact_name, 0, 2, 1, 1)

        self.txt_company_name = QLineEdit(self.scrollContents_company)
        self.txt_company_name.setObjectName(u"txt_company_name")
        self.txt_company_name.setMinimumSize(QSize(0, 36))
        self.txt_company_name.setMaximumSize(QSize(16777215, 36))

        self.grid_company_form.addWidget(self.txt_company_name, 1, 0, 1, 2)

        self.txt_contact_name = QLineEdit(self.scrollContents_company)
        self.txt_contact_name.setObjectName(u"txt_contact_name")
        self.txt_contact_name.setMinimumSize(QSize(0, 36))
        self.txt_contact_name.setMaximumSize(QSize(16777215, 36))

        self.grid_company_form.addWidget(self.txt_contact_name, 1, 2, 1, 1)

        self.lbl_company_email = QLabel(self.scrollContents_company)
        self.lbl_company_email.setObjectName(u"lbl_company_email")

        self.grid_company_form.addWidget(self.lbl_company_email, 2, 0, 1, 1)

        self.lbl_company_phone = QLabel(self.scrollContents_company)
        self.lbl_company_phone.setObjectName(u"lbl_company_phone")

        self.grid_company_form.addWidget(self.lbl_company_phone, 2, 1, 1, 1)

        self.lbl_company_phone2 = QLabel(self.scrollContents_company)
        self.lbl_company_phone2.setObjectName(u"lbl_company_phone2")

        self.grid_company_form.addWidget(self.lbl_company_phone2, 2, 2, 1, 1)

        self.txt_company_email = QLineEdit(self.scrollContents_company)
        self.txt_company_email.setObjectName(u"txt_company_email")
        self.txt_company_email.setMinimumSize(QSize(0, 36))
        self.txt_company_email.setMaximumSize(QSize(16777215, 36))

        self.grid_company_form.addWidget(self.txt_company_email, 3, 0, 1, 1)

        self.txt_company_phone = QLineEdit(self.scrollContents_company)
        self.txt_company_phone.setObjectName(u"txt_company_phone")
        self.txt_company_phone.setMinimumSize(QSize(0, 36))
        self.txt_company_phone.setMaximumSize(QSize(16777215, 36))

        self.grid_company_form.addWidget(self.txt_company_phone, 3, 1, 1, 1)

        self.txt_company_phone2 = QLineEdit(self.scrollContents_company)
        self.txt_company_phone2.setObjectName(u"txt_company_phone2")
        self.txt_company_phone2.setMinimumSize(QSize(0, 36))
        self.txt_company_phone2.setMaximumSize(QSize(16777215, 36))

        self.grid_company_form.addWidget(self.txt_company_phone2, 3, 2, 1, 1)

        self.div_company_1 = QFrame(self.scrollContents_company)
        self.div_company_1.setObjectName(u"div_company_1")
        self.div_company_1.setMaximumSize(QSize(16777215, 1))

        self.grid_company_form.addWidget(self.div_company_1, 4, 0, 1, 3)

        self.lbl_company_address = QLabel(self.scrollContents_company)
        self.lbl_company_address.setObjectName(u"lbl_company_address")

        self.grid_company_form.addWidget(self.lbl_company_address, 5, 0, 1, 2)

        self.lbl_company_address2 = QLabel(self.scrollContents_company)
        self.lbl_company_address2.setObjectName(u"lbl_company_address2")

        self.grid_company_form.addWidget(self.lbl_company_address2, 5, 2, 1, 1)

        self.txt_company_address = QLineEdit(self.scrollContents_company)
        self.txt_company_address.setObjectName(u"txt_company_address")
        self.txt_company_address.setMinimumSize(QSize(0, 36))
        self.txt_company_address.setMaximumSize(QSize(16777215, 36))

        self.grid_company_form.addWidget(self.txt_company_address, 6, 0, 1, 2)

        self.txt_company_address2 = QLineEdit(self.scrollContents_company)
        self.txt_company_address2.setObjectName(u"txt_company_address2")
        self.txt_company_address2.setMinimumSize(QSize(0, 36))
        self.txt_company_address2.setMaximumSize(QSize(16777215, 36))

        self.grid_company_form.addWidget(self.txt_company_address2, 6, 2, 1, 1)

        self.lbl_company_city = QLabel(self.scrollContents_company)
        self.lbl_company_city.setObjectName(u"lbl_company_city")

        self.grid_company_form.addWidget(self.lbl_company_city, 7, 0, 1, 1)

        self.lbl_company_state = QLabel(self.scrollContents_company)
        self.lbl_company_state.setObjectName(u"lbl_company_state")

        self.grid_company_form.addWidget(self.lbl_company_state, 7, 1, 1, 1)

        self.lbl_company_zip = QLabel(self.scrollContents_company)
        self.lbl_company_zip.setObjectName(u"lbl_company_zip")

        self.grid_company_form.addWidget(self.lbl_company_zip, 7, 2, 1, 1)

        self.cmb_company_city = QComboBox(self.scrollContents_company)
        self.cmb_company_city.setObjectName(u"cmb_company_city")
        self.cmb_company_city.setMinimumSize(QSize(0, 46))
        self.cmb_company_city.setMaximumSize(QSize(16777215, 16777215))

        self.grid_company_form.addWidget(self.cmb_company_city, 8, 0, 1, 1)

        self.cmb_company_state = QComboBox(self.scrollContents_company)
        self.cmb_company_state.setObjectName(u"cmb_company_state")
        self.cmb_company_state.setMinimumSize(QSize(0, 46))
        self.cmb_company_state.setMaximumSize(QSize(16777215, 16777215))

        self.grid_company_form.addWidget(self.cmb_company_state, 8, 1, 1, 1)

        self.txt_company_zip = QLineEdit(self.scrollContents_company)
        self.txt_company_zip.setObjectName(u"txt_company_zip")
        self.txt_company_zip.setMinimumSize(QSize(0, 36))
        self.txt_company_zip.setMaximumSize(QSize(16777215, 36))

        self.grid_company_form.addWidget(self.txt_company_zip, 8, 2, 1, 1)

        self.div_company_2 = QFrame(self.scrollContents_company)
        self.div_company_2.setObjectName(u"div_company_2")
        self.div_company_2.setMaximumSize(QSize(16777215, 1))

        self.grid_company_form.addWidget(self.div_company_2, 9, 0, 1, 3)

        self.lbl_company_website = QLabel(self.scrollContents_company)
        self.lbl_company_website.setObjectName(u"lbl_company_website")

        self.grid_company_form.addWidget(self.lbl_company_website, 10, 0, 1, 2)

        self.lbl_company_status = QLabel(self.scrollContents_company)
        self.lbl_company_status.setObjectName(u"lbl_company_status")

        self.grid_company_form.addWidget(self.lbl_company_status, 10, 2, 1, 1)

        self.txt_company_website = QLineEdit(self.scrollContents_company)
        self.txt_company_website.setObjectName(u"txt_company_website")
        self.txt_company_website.setMinimumSize(QSize(0, 36))
        self.txt_company_website.setMaximumSize(QSize(16777215, 36))

        self.grid_company_form.addWidget(self.txt_company_website, 11, 0, 1, 2)

        self.cmb_company_status = QComboBox(self.scrollContents_company)
        self.cmb_company_status.addItem("")
        self.cmb_company_status.addItem("")
        self.cmb_company_status.setObjectName(u"cmb_company_status")
        self.cmb_company_status.setMinimumSize(QSize(0, 46))
        self.cmb_company_status.setMaximumSize(QSize(16777215, 16777215))

        self.grid_company_form.addWidget(self.cmb_company_status, 11, 2, 1, 1)

        self.lbl_company_instagram = QLabel(self.scrollContents_company)
        self.lbl_company_instagram.setObjectName(u"lbl_company_instagram")

        self.grid_company_form.addWidget(self.lbl_company_instagram, 12, 0, 1, 1)

        self.lbl_company_facebook = QLabel(self.scrollContents_company)
        self.lbl_company_facebook.setObjectName(u"lbl_company_facebook")

        self.grid_company_form.addWidget(self.lbl_company_facebook, 12, 1, 1, 1)

        self.lbl_company_linkedin = QLabel(self.scrollContents_company)
        self.lbl_company_linkedin.setObjectName(u"lbl_company_linkedin")

        self.grid_company_form.addWidget(self.lbl_company_linkedin, 12, 2, 1, 1)

        self.txt_company_instagram = QLineEdit(self.scrollContents_company)
        self.txt_company_instagram.setObjectName(u"txt_company_instagram")
        self.txt_company_instagram.setMinimumSize(QSize(0, 36))
        self.txt_company_instagram.setMaximumSize(QSize(16777215, 36))

        self.grid_company_form.addWidget(self.txt_company_instagram, 13, 0, 1, 1)

        self.txt_company_facebook = QLineEdit(self.scrollContents_company)
        self.txt_company_facebook.setObjectName(u"txt_company_facebook")
        self.txt_company_facebook.setMinimumSize(QSize(0, 36))
        self.txt_company_facebook.setMaximumSize(QSize(16777215, 36))

        self.grid_company_form.addWidget(self.txt_company_facebook, 13, 1, 1, 1)

        self.txt_company_linkedin = QLineEdit(self.scrollContents_company)
        self.txt_company_linkedin.setObjectName(u"txt_company_linkedin")
        self.txt_company_linkedin.setMinimumSize(QSize(0, 36))
        self.txt_company_linkedin.setMaximumSize(QSize(16777215, 36))

        self.grid_company_form.addWidget(self.txt_company_linkedin, 13, 2, 1, 1)

        self.lbl_company_twitter = QLabel(self.scrollContents_company)
        self.lbl_company_twitter.setObjectName(u"lbl_company_twitter")

        self.grid_company_form.addWidget(self.lbl_company_twitter, 14, 0, 1, 1)

        self.lbl_company_notes = QLabel(self.scrollContents_company)
        self.lbl_company_notes.setObjectName(u"lbl_company_notes")

        self.grid_company_form.addWidget(self.lbl_company_notes, 14, 1, 1, 2)

        self.txt_company_twitter = QLineEdit(self.scrollContents_company)
        self.txt_company_twitter.setObjectName(u"txt_company_twitter")
        self.txt_company_twitter.setMinimumSize(QSize(0, 36))
        self.txt_company_twitter.setMaximumSize(QSize(16777215, 36))

        self.grid_company_form.addWidget(self.txt_company_twitter, 15, 0, 1, 1)

        self.txt_company_notes = QTextEdit(self.scrollContents_company)
        self.txt_company_notes.setObjectName(u"txt_company_notes")
        self.txt_company_notes.setMinimumSize(QSize(0, 70))
        self.txt_company_notes.setMaximumSize(QSize(16777215, 90))

        self.grid_company_form.addWidget(self.txt_company_notes, 15, 1, 1, 2)

        self.txt_company_id = QLineEdit(self.scrollContents_company)
        self.txt_company_id.setObjectName(u"txt_company_id")
        self.txt_company_id.setMinimumSize(QSize(0, 36))
        self.txt_company_id.setMaximumSize(QSize(16777215, 36))
        self.txt_company_id.setVisible(False)
        self.txt_company_id.setReadOnly(True)

        self.grid_company_form.addWidget(self.txt_company_id, 16, 0, 1, 1)

        self.scroll_company_form.setWidget(self.scrollContents_company)

        self.layout_company_card.addWidget(self.scroll_company_form)

        self.frame_company_footer = QFrame(self.frame_company_card)
        self.frame_company_footer.setObjectName(u"frame_company_footer")
        self.hboxLayout6 = QHBoxLayout(self.frame_company_footer)
        self.hboxLayout6.setObjectName(u"hboxLayout6")
        self.hboxLayout6.setContentsMargins(20, 12, 20, 12)
        self.spacerItem8 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout6.addItem(self.spacerItem8)

        self.btn_delete_company = QPushButton(self.frame_company_footer)
        self.btn_delete_company.setObjectName(u"btn_delete_company")
        self.btn_delete_company.setMinimumSize(QSize(90, 36))
        self.btn_delete_company.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout6.addWidget(self.btn_delete_company)

        self.btn_save_company = QPushButton(self.frame_company_footer)
        self.btn_save_company.setObjectName(u"btn_save_company")
        self.btn_save_company.setMinimumSize(QSize(110, 36))
        self.btn_save_company.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout6.addWidget(self.btn_save_company)


        self.layout_company_card.addWidget(self.frame_company_footer)


        self.layout_companies_right_panel.addWidget(self.frame_company_card)

        self.spacerItem9 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_companies_right_panel.addItem(self.spacerItem9)


        self.layout_tab_companies_master.addLayout(self.layout_companies_right_panel)

        self.tabWidget_companies_page.addTab(self.tab_companies_master, "")

        self.layout_companies_page.addWidget(self.tabWidget_companies_page)

        self.Pages.addWidget(self.pg_companies)
        self.pg_contractors = QWidget()
        self.pg_contractors.setObjectName(u"pg_contractors")
        self.layout_contractors_page = QVBoxLayout(self.pg_contractors)
        self.layout_contractors_page.setSpacing(0)
        self.layout_contractors_page.setObjectName(u"layout_contractors_page")
        self.layout_contractors_page.setContentsMargins(0, 0, 0, 0)
        self.tabWidget_contractors_page = QTabWidget(self.pg_contractors)
        self.tabWidget_contractors_page.setObjectName(u"tabWidget_contractors_page")
        self.tab_contractors_master = QWidget()
        self.tab_contractors_master.setObjectName(u"tab_contractors_master")
        self.layout_tab_contractors_master = QHBoxLayout(self.tab_contractors_master)
        self.layout_tab_contractors_master.setSpacing(16)
        self.layout_tab_contractors_master.setObjectName(u"layout_tab_contractors_master")
        self.layout_tab_contractors_master.setContentsMargins(16, 16, 16, 16)
        self.layout_contractors_left_panel = QVBoxLayout()
        self.layout_contractors_left_panel.setSpacing(10)
        self.layout_contractors_left_panel.setObjectName(u"layout_contractors_left_panel")
        self.layout_contractors_left_panel.setContentsMargins(0, 0, 0, 0)
        self.layout_contractors_row_search = QHBoxLayout()
        self.layout_contractors_row_search.setSpacing(8)
        self.layout_contractors_row_search.setObjectName(u"layout_contractors_row_search")
        self.txt_search_contractors = QLineEdit(self.tab_contractors_master)
        self.txt_search_contractors.setObjectName(u"txt_search_contractors")
        self.txt_search_contractors.setMinimumSize(QSize(280, 36))

        self.layout_contractors_row_search.addWidget(self.txt_search_contractors)


        self.layout_contractors_left_panel.addLayout(self.layout_contractors_row_search)

        self.layout_contractors_row_filters = QHBoxLayout()
        self.layout_contractors_row_filters.setSpacing(8)
        self.layout_contractors_row_filters.setObjectName(u"layout_contractors_row_filters")
        self.cmb_filter_contractor_status = QComboBox(self.tab_contractors_master)
        self.cmb_filter_contractor_status.addItem("")
        self.cmb_filter_contractor_status.addItem("")
        self.cmb_filter_contractor_status.addItem("")
        self.cmb_filter_contractor_status.addItem("")
        self.cmb_filter_contractor_status.setObjectName(u"cmb_filter_contractor_status")
        self.cmb_filter_contractor_status.setMinimumSize(QSize(140, 46))
        self.cmb_filter_contractor_status.setMaximumSize(QSize(16777215, 16777215))

        self.layout_contractors_row_filters.addWidget(self.cmb_filter_contractor_status)

        self.btn_refresh_contractors = QPushButton(self.tab_contractors_master)
        self.btn_refresh_contractors.setObjectName(u"btn_refresh_contractors")
        self.btn_refresh_contractors.setMinimumSize(QSize(90, 36))
        self.btn_refresh_contractors.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_contractors_row_filters.addWidget(self.btn_refresh_contractors)


        self.layout_contractors_left_panel.addLayout(self.layout_contractors_row_filters)

        self.layout_contractors_row_export = QHBoxLayout()
        self.layout_contractors_row_export.setSpacing(8)
        self.layout_contractors_row_export.setObjectName(u"layout_contractors_row_export")
        self.btn_export_excel_contractors = QPushButton(self.tab_contractors_master)
        self.btn_export_excel_contractors.setObjectName(u"btn_export_excel_contractors")
        self.btn_export_excel_contractors.setMinimumSize(QSize(110, 36))
        self.btn_export_excel_contractors.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_contractors_row_export.addWidget(self.btn_export_excel_contractors)

        self.btn_export_pdf_contractors = QPushButton(self.tab_contractors_master)
        self.btn_export_pdf_contractors.setObjectName(u"btn_export_pdf_contractors")
        self.btn_export_pdf_contractors.setMinimumSize(QSize(100, 36))
        self.btn_export_pdf_contractors.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_contractors_row_export.addWidget(self.btn_export_pdf_contractors)


        self.layout_contractors_left_panel.addLayout(self.layout_contractors_row_export)

        self.layout_contractors_row_actions = QHBoxLayout()
        self.layout_contractors_row_actions.setSpacing(8)
        self.layout_contractors_row_actions.setObjectName(u"layout_contractors_row_actions")
        self.btn_new_contractor = QPushButton(self.tab_contractors_master)
        self.btn_new_contractor.setObjectName(u"btn_new_contractor")
        self.btn_new_contractor.setMinimumSize(QSize(140, 36))
        self.btn_new_contractor.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_contractors_row_actions.addWidget(self.btn_new_contractor)


        self.layout_contractors_left_panel.addLayout(self.layout_contractors_row_actions)

        self.btn_toggle_contractors_table_expanded = QPushButton(self.tab_contractors_master)
        self.btn_toggle_contractors_table_expanded.setObjectName(u"btn_toggle_contractors_table_expanded")
        self.btn_toggle_contractors_table_expanded.setMinimumSize(QSize(0, 34))
        self.btn_toggle_contractors_table_expanded.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle_contractors_table_expanded.setStyleSheet(u"QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; border-radius: 6px; font-size: 12px; font-weight: 600; } QPushButton:hover { background-color: #E1E8F0; }")

        self.layout_contractors_left_panel.addWidget(self.btn_toggle_contractors_table_expanded)

        self.table_contractors = QTableWidget(self.tab_contractors_master)
        if (self.table_contractors.columnCount() < 10):
            self.table_contractors.setColumnCount(10)
        __qtablewidgetitem36 = QTableWidgetItem()
        self.table_contractors.setHorizontalHeaderItem(0, __qtablewidgetitem36)
        __qtablewidgetitem37 = QTableWidgetItem()
        self.table_contractors.setHorizontalHeaderItem(1, __qtablewidgetitem37)
        __qtablewidgetitem38 = QTableWidgetItem()
        self.table_contractors.setHorizontalHeaderItem(2, __qtablewidgetitem38)
        __qtablewidgetitem39 = QTableWidgetItem()
        self.table_contractors.setHorizontalHeaderItem(3, __qtablewidgetitem39)
        __qtablewidgetitem40 = QTableWidgetItem()
        self.table_contractors.setHorizontalHeaderItem(4, __qtablewidgetitem40)
        __qtablewidgetitem41 = QTableWidgetItem()
        self.table_contractors.setHorizontalHeaderItem(5, __qtablewidgetitem41)
        __qtablewidgetitem42 = QTableWidgetItem()
        self.table_contractors.setHorizontalHeaderItem(6, __qtablewidgetitem42)
        __qtablewidgetitem43 = QTableWidgetItem()
        self.table_contractors.setHorizontalHeaderItem(7, __qtablewidgetitem43)
        __qtablewidgetitem44 = QTableWidgetItem()
        self.table_contractors.setHorizontalHeaderItem(8, __qtablewidgetitem44)
        __qtablewidgetitem45 = QTableWidgetItem()
        self.table_contractors.setHorizontalHeaderItem(9, __qtablewidgetitem45)
        self.table_contractors.setObjectName(u"table_contractors")
        self.table_contractors.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_contractors.setAlternatingRowColors(True)
        self.table_contractors.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_contractors.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_contractors.setSortingEnabled(True)
        self.table_contractors.setColumnCount(10)
        self.table_contractors.horizontalHeader().setStretchLastSection(True)

        self.layout_contractors_left_panel.addWidget(self.table_contractors)


        self.layout_tab_contractors_master.addLayout(self.layout_contractors_left_panel)

        self.layout_contractors_right_panel = QVBoxLayout()
        self.layout_contractors_right_panel.setSpacing(0)
        self.layout_contractors_right_panel.setObjectName(u"layout_contractors_right_panel")
        self.layout_contractors_right_panel.setContentsMargins(0, 0, 0, 0)
        self.frame_contractor_card = QFrame(self.tab_contractors_master)
        self.frame_contractor_card.setObjectName(u"frame_contractor_card")
        self.frame_contractor_card.setMaximumSize(QSize(860, 16777215))
        self.layout_contractor_card = QVBoxLayout(self.frame_contractor_card)
        self.layout_contractor_card.setSpacing(0)
        self.layout_contractor_card.setObjectName(u"layout_contractor_card")
        self.layout_contractor_card.setContentsMargins(0, 0, 0, 0)
        self.card_header_contractor = QFrame(self.frame_contractor_card)
        self.card_header_contractor.setObjectName(u"card_header_contractor")
        self.hboxLayout7 = QHBoxLayout(self.card_header_contractor)
        self.hboxLayout7.setObjectName(u"hboxLayout7")
        self.hboxLayout7.setContentsMargins(20, -1, -1, -1)
        self.lbl_contractor_form_title = QLabel(self.card_header_contractor)
        self.lbl_contractor_form_title.setObjectName(u"lbl_contractor_form_title")

        self.hboxLayout7.addWidget(self.lbl_contractor_form_title)

        self.spacerItem10 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout7.addItem(self.spacerItem10)

        self.lbl_contractor_id_display = QLabel(self.card_header_contractor)
        self.lbl_contractor_id_display.setObjectName(u"lbl_contractor_id_display")

        self.hboxLayout7.addWidget(self.lbl_contractor_id_display)


        self.layout_contractor_card.addWidget(self.card_header_contractor)

        self.scroll_contractor_form = QScrollArea(self.frame_contractor_card)
        self.scroll_contractor_form.setObjectName(u"scroll_contractor_form")
        self.scroll_contractor_form.setFrameShape(QFrame.NoFrame)
        self.scroll_contractor_form.setWidgetResizable(True)
        self.scrollContents_contractor = QWidget()
        self.scrollContents_contractor.setObjectName(u"scrollContents_contractor")
        self.scrollContents_contractor.setGeometry(QRect(0, 0, 852, 836))
        self.grid_contractor_form = QGridLayout(self.scrollContents_contractor)
        self.grid_contractor_form.setObjectName(u"grid_contractor_form")
        self.grid_contractor_form.setHorizontalSpacing(16)
        self.grid_contractor_form.setVerticalSpacing(10)
        self.grid_contractor_form.setContentsMargins(20, 16, 20, 16)
        self.lbl_contractor_full_name = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_full_name.setObjectName(u"lbl_contractor_full_name")

        self.grid_contractor_form.addWidget(self.lbl_contractor_full_name, 0, 0, 1, 2)

        self.lbl_contractor_position = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_position.setObjectName(u"lbl_contractor_position")

        self.grid_contractor_form.addWidget(self.lbl_contractor_position, 0, 2, 1, 1)

        self.txt_contractor_full_name = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_full_name.setObjectName(u"txt_contractor_full_name")
        self.txt_contractor_full_name.setMinimumSize(QSize(0, 36))
        self.txt_contractor_full_name.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_full_name, 1, 0, 1, 2)

        self.txt_contractor_position = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_position.setObjectName(u"txt_contractor_position")
        self.txt_contractor_position.setMinimumSize(QSize(0, 36))
        self.txt_contractor_position.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_position, 1, 2, 1, 1)

        self.lbl_contractor_email = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_email.setObjectName(u"lbl_contractor_email")

        self.grid_contractor_form.addWidget(self.lbl_contractor_email, 2, 0, 1, 1)

        self.lbl_contractor_phone = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_phone.setObjectName(u"lbl_contractor_phone")

        self.grid_contractor_form.addWidget(self.lbl_contractor_phone, 2, 1, 1, 1)

        self.lbl_contractor_phone2 = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_phone2.setObjectName(u"lbl_contractor_phone2")

        self.grid_contractor_form.addWidget(self.lbl_contractor_phone2, 2, 2, 1, 1)

        self.txt_contractor_email = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_email.setObjectName(u"txt_contractor_email")
        self.txt_contractor_email.setMinimumSize(QSize(0, 36))
        self.txt_contractor_email.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_email, 3, 0, 1, 1)

        self.txt_contractor_phone = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_phone.setObjectName(u"txt_contractor_phone")
        self.txt_contractor_phone.setMinimumSize(QSize(0, 36))
        self.txt_contractor_phone.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_phone, 3, 1, 1, 1)

        self.txt_contractor_phone2 = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_phone2.setObjectName(u"txt_contractor_phone2")
        self.txt_contractor_phone2.setMinimumSize(QSize(0, 36))
        self.txt_contractor_phone2.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_phone2, 3, 2, 1, 1)

        self.div_contractor_1 = QFrame(self.scrollContents_contractor)
        self.div_contractor_1.setObjectName(u"div_contractor_1")
        self.div_contractor_1.setMaximumSize(QSize(16777215, 1))

        self.grid_contractor_form.addWidget(self.div_contractor_1, 4, 0, 1, 3)

        self.lbl_contractor_company_name = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_company_name.setObjectName(u"lbl_contractor_company_name")

        self.grid_contractor_form.addWidget(self.lbl_contractor_company_name, 5, 0, 1, 2)

        self.lbl_contractor_company_email = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_company_email.setObjectName(u"lbl_contractor_company_email")

        self.grid_contractor_form.addWidget(self.lbl_contractor_company_email, 5, 2, 1, 1)

        self.txt_contractor_company_name = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_company_name.setObjectName(u"txt_contractor_company_name")
        self.txt_contractor_company_name.setMinimumSize(QSize(0, 36))
        self.txt_contractor_company_name.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_company_name, 6, 0, 1, 2)

        self.txt_contractor_company_email = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_company_email.setObjectName(u"txt_contractor_company_email")
        self.txt_contractor_company_email.setMinimumSize(QSize(0, 36))
        self.txt_contractor_company_email.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_company_email, 6, 2, 1, 1)

        self.lbl_contractor_company_phone = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_company_phone.setObjectName(u"lbl_contractor_company_phone")

        self.grid_contractor_form.addWidget(self.lbl_contractor_company_phone, 7, 0, 1, 1)

        self.lbl_contractor_company_phone2 = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_company_phone2.setObjectName(u"lbl_contractor_company_phone2")

        self.grid_contractor_form.addWidget(self.lbl_contractor_company_phone2, 7, 1, 1, 1)

        self.txt_contractor_company_phone = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_company_phone.setObjectName(u"txt_contractor_company_phone")
        self.txt_contractor_company_phone.setMinimumSize(QSize(0, 36))
        self.txt_contractor_company_phone.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_company_phone, 8, 0, 1, 1)

        self.txt_contractor_company_phone2 = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_company_phone2.setObjectName(u"txt_contractor_company_phone2")
        self.txt_contractor_company_phone2.setMinimumSize(QSize(0, 36))
        self.txt_contractor_company_phone2.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_company_phone2, 8, 1, 1, 1)

        self.div_contractor_2 = QFrame(self.scrollContents_contractor)
        self.div_contractor_2.setObjectName(u"div_contractor_2")
        self.div_contractor_2.setMaximumSize(QSize(16777215, 1))

        self.grid_contractor_form.addWidget(self.div_contractor_2, 9, 0, 1, 3)

        self.lbl_contractor_address = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_address.setObjectName(u"lbl_contractor_address")

        self.grid_contractor_form.addWidget(self.lbl_contractor_address, 10, 0, 1, 2)

        self.lbl_contractor_address2 = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_address2.setObjectName(u"lbl_contractor_address2")

        self.grid_contractor_form.addWidget(self.lbl_contractor_address2, 10, 2, 1, 1)

        self.txt_contractor_address = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_address.setObjectName(u"txt_contractor_address")
        self.txt_contractor_address.setMinimumSize(QSize(0, 36))
        self.txt_contractor_address.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_address, 11, 0, 1, 2)

        self.txt_contractor_address2 = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_address2.setObjectName(u"txt_contractor_address2")
        self.txt_contractor_address2.setMinimumSize(QSize(0, 36))
        self.txt_contractor_address2.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_address2, 11, 2, 1, 1)

        self.lbl_contractor_city = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_city.setObjectName(u"lbl_contractor_city")

        self.grid_contractor_form.addWidget(self.lbl_contractor_city, 12, 0, 1, 1)

        self.lbl_contractor_state = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_state.setObjectName(u"lbl_contractor_state")

        self.grid_contractor_form.addWidget(self.lbl_contractor_state, 12, 1, 1, 1)

        self.lbl_contractor_zip = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_zip.setObjectName(u"lbl_contractor_zip")

        self.grid_contractor_form.addWidget(self.lbl_contractor_zip, 12, 2, 1, 1)

        self.cmb_contractor_city = QComboBox(self.scrollContents_contractor)
        self.cmb_contractor_city.setObjectName(u"cmb_contractor_city")
        self.cmb_contractor_city.setMinimumSize(QSize(0, 46))
        self.cmb_contractor_city.setMaximumSize(QSize(16777215, 16777215))

        self.grid_contractor_form.addWidget(self.cmb_contractor_city, 13, 0, 1, 1)

        self.cmb_contractor_state = QComboBox(self.scrollContents_contractor)
        self.cmb_contractor_state.setObjectName(u"cmb_contractor_state")
        self.cmb_contractor_state.setMinimumSize(QSize(0, 46))
        self.cmb_contractor_state.setMaximumSize(QSize(16777215, 16777215))

        self.grid_contractor_form.addWidget(self.cmb_contractor_state, 13, 1, 1, 1)

        self.txt_contractor_zip = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_zip.setObjectName(u"txt_contractor_zip")
        self.txt_contractor_zip.setMinimumSize(QSize(0, 36))
        self.txt_contractor_zip.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_zip, 13, 2, 1, 1)

        self.div_contractor_3 = QFrame(self.scrollContents_contractor)
        self.div_contractor_3.setObjectName(u"div_contractor_3")
        self.div_contractor_3.setMaximumSize(QSize(16777215, 1))

        self.grid_contractor_form.addWidget(self.div_contractor_3, 14, 0, 1, 3)

        self.lbl_contractor_website = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_website.setObjectName(u"lbl_contractor_website")

        self.grid_contractor_form.addWidget(self.lbl_contractor_website, 15, 0, 1, 2)

        self.lbl_contractor_status = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_status.setObjectName(u"lbl_contractor_status")

        self.grid_contractor_form.addWidget(self.lbl_contractor_status, 15, 2, 1, 1)

        self.txt_contractor_website = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_website.setObjectName(u"txt_contractor_website")
        self.txt_contractor_website.setMinimumSize(QSize(0, 36))
        self.txt_contractor_website.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_website, 16, 0, 1, 2)

        self.cmb_contractor_status = QComboBox(self.scrollContents_contractor)
        self.cmb_contractor_status.addItem("")
        self.cmb_contractor_status.addItem("")
        self.cmb_contractor_status.addItem("")
        self.cmb_contractor_status.setObjectName(u"cmb_contractor_status")
        self.cmb_contractor_status.setMinimumSize(QSize(0, 46))
        self.cmb_contractor_status.setMaximumSize(QSize(16777215, 16777215))

        self.grid_contractor_form.addWidget(self.cmb_contractor_status, 16, 2, 1, 1)

        self.lbl_contractor_instagram = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_instagram.setObjectName(u"lbl_contractor_instagram")

        self.grid_contractor_form.addWidget(self.lbl_contractor_instagram, 17, 0, 1, 1)

        self.lbl_contractor_facebook = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_facebook.setObjectName(u"lbl_contractor_facebook")

        self.grid_contractor_form.addWidget(self.lbl_contractor_facebook, 17, 1, 1, 1)

        self.lbl_contractor_linkedin = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_linkedin.setObjectName(u"lbl_contractor_linkedin")

        self.grid_contractor_form.addWidget(self.lbl_contractor_linkedin, 17, 2, 1, 1)

        self.txt_contractor_instagram = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_instagram.setObjectName(u"txt_contractor_instagram")
        self.txt_contractor_instagram.setMinimumSize(QSize(0, 36))
        self.txt_contractor_instagram.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_instagram, 18, 0, 1, 1)

        self.txt_contractor_facebook = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_facebook.setObjectName(u"txt_contractor_facebook")
        self.txt_contractor_facebook.setMinimumSize(QSize(0, 36))
        self.txt_contractor_facebook.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_facebook, 18, 1, 1, 1)

        self.txt_contractor_linkedin = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_linkedin.setObjectName(u"txt_contractor_linkedin")
        self.txt_contractor_linkedin.setMinimumSize(QSize(0, 36))
        self.txt_contractor_linkedin.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_linkedin, 18, 2, 1, 1)

        self.lbl_contractor_twitter = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_twitter.setObjectName(u"lbl_contractor_twitter")

        self.grid_contractor_form.addWidget(self.lbl_contractor_twitter, 19, 0, 1, 1)

        self.lbl_contractor_notes = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_notes.setObjectName(u"lbl_contractor_notes")

        self.grid_contractor_form.addWidget(self.lbl_contractor_notes, 19, 1, 1, 2)

        self.txt_contractor_twitter = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_twitter.setObjectName(u"txt_contractor_twitter")
        self.txt_contractor_twitter.setMinimumSize(QSize(0, 36))
        self.txt_contractor_twitter.setMaximumSize(QSize(16777215, 36))

        self.grid_contractor_form.addWidget(self.txt_contractor_twitter, 20, 0, 1, 1)

        self.txt_contractor_notes = QTextEdit(self.scrollContents_contractor)
        self.txt_contractor_notes.setObjectName(u"txt_contractor_notes")
        self.txt_contractor_notes.setMinimumSize(QSize(0, 70))
        self.txt_contractor_notes.setMaximumSize(QSize(16777215, 90))

        self.grid_contractor_form.addWidget(self.txt_contractor_notes, 20, 1, 1, 2)

        self.txt_contractor_id = QLineEdit(self.scrollContents_contractor)
        self.txt_contractor_id.setObjectName(u"txt_contractor_id")
        self.txt_contractor_id.setMinimumSize(QSize(0, 36))
        self.txt_contractor_id.setMaximumSize(QSize(16777215, 36))
        self.txt_contractor_id.setVisible(False)
        self.txt_contractor_id.setReadOnly(True)

        self.grid_contractor_form.addWidget(self.txt_contractor_id, 21, 0, 1, 1)

        self.lbl_contractor_payment_cycle_type = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_payment_cycle_type.setObjectName(u"lbl_contractor_payment_cycle_type")

        self.grid_contractor_form.addWidget(self.lbl_contractor_payment_cycle_type, 22, 0, 1, 1)

        self.lbl_contractor_payment_cycle_weekday = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_payment_cycle_weekday.setObjectName(u"lbl_contractor_payment_cycle_weekday")

        self.grid_contractor_form.addWidget(self.lbl_contractor_payment_cycle_weekday, 22, 1, 1, 1)

        self.lbl_contractor_payment_cycle_days = QLabel(self.scrollContents_contractor)
        self.lbl_contractor_payment_cycle_days.setObjectName(u"lbl_contractor_payment_cycle_days")

        self.grid_contractor_form.addWidget(self.lbl_contractor_payment_cycle_days, 22, 2, 1, 1)

        self.cmb_contractor_payment_cycle_type = QComboBox(self.scrollContents_contractor)
        self.cmb_contractor_payment_cycle_type.addItem("")
        self.cmb_contractor_payment_cycle_type.addItem("")
        self.cmb_contractor_payment_cycle_type.addItem("")
        self.cmb_contractor_payment_cycle_type.setObjectName(u"cmb_contractor_payment_cycle_type")
        self.cmb_contractor_payment_cycle_type.setMinimumSize(QSize(0, 46))

        self.grid_contractor_form.addWidget(self.cmb_contractor_payment_cycle_type, 23, 0, 1, 1)

        self.cmb_contractor_payment_cycle_weekday = QComboBox(self.scrollContents_contractor)
        self.cmb_contractor_payment_cycle_weekday.addItem("")
        self.cmb_contractor_payment_cycle_weekday.addItem("")
        self.cmb_contractor_payment_cycle_weekday.addItem("")
        self.cmb_contractor_payment_cycle_weekday.addItem("")
        self.cmb_contractor_payment_cycle_weekday.addItem("")
        self.cmb_contractor_payment_cycle_weekday.addItem("")
        self.cmb_contractor_payment_cycle_weekday.addItem("")
        self.cmb_contractor_payment_cycle_weekday.setObjectName(u"cmb_contractor_payment_cycle_weekday")
        self.cmb_contractor_payment_cycle_weekday.setMinimumSize(QSize(0, 46))

        self.grid_contractor_form.addWidget(self.cmb_contractor_payment_cycle_weekday, 23, 1, 1, 1)

        self.spin_contractor_payment_cycle_days = QSpinBox(self.scrollContents_contractor)
        self.spin_contractor_payment_cycle_days.setObjectName(u"spin_contractor_payment_cycle_days")
        self.spin_contractor_payment_cycle_days.setMinimumSize(QSize(0, 46))
        self.spin_contractor_payment_cycle_days.setMinimum(1)
        self.spin_contractor_payment_cycle_days.setMaximum(180)
        self.spin_contractor_payment_cycle_days.setValue(30)

        self.grid_contractor_form.addWidget(self.spin_contractor_payment_cycle_days, 23, 2, 1, 1)

        self.scroll_contractor_form.setWidget(self.scrollContents_contractor)

        self.layout_contractor_card.addWidget(self.scroll_contractor_form)

        self.frame_contractor_footer = QFrame(self.frame_contractor_card)
        self.frame_contractor_footer.setObjectName(u"frame_contractor_footer")
        self.hboxLayout8 = QHBoxLayout(self.frame_contractor_footer)
        self.hboxLayout8.setObjectName(u"hboxLayout8")
        self.hboxLayout8.setContentsMargins(20, 12, 20, 12)
        self.spacerItem11 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout8.addItem(self.spacerItem11)

        self.btn_delete_contractor = QPushButton(self.frame_contractor_footer)
        self.btn_delete_contractor.setObjectName(u"btn_delete_contractor")
        self.btn_delete_contractor.setMinimumSize(QSize(90, 36))
        self.btn_delete_contractor.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout8.addWidget(self.btn_delete_contractor)

        self.btn_save_contractor = QPushButton(self.frame_contractor_footer)
        self.btn_save_contractor.setObjectName(u"btn_save_contractor")
        self.btn_save_contractor.setMinimumSize(QSize(110, 36))
        self.btn_save_contractor.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout8.addWidget(self.btn_save_contractor)


        self.layout_contractor_card.addWidget(self.frame_contractor_footer)


        self.layout_contractors_right_panel.addWidget(self.frame_contractor_card)

        self.spacerItem12 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_contractors_right_panel.addItem(self.spacerItem12)


        self.layout_tab_contractors_master.addLayout(self.layout_contractors_right_panel)

        self.tabWidget_contractors_page.addTab(self.tab_contractors_master, "")

        self.layout_contractors_page.addWidget(self.tabWidget_contractors_page)

        self.Pages.addWidget(self.pg_contractors)
        self.pg_work_types = QWidget()
        self.pg_work_types.setObjectName(u"pg_work_types")
        self.layout_work_types_page = QVBoxLayout(self.pg_work_types)
        self.layout_work_types_page.setSpacing(0)
        self.layout_work_types_page.setObjectName(u"layout_work_types_page")
        self.layout_work_types_page.setContentsMargins(0, 0, 0, 0)
        self.tabWidget_work_types_page = QTabWidget(self.pg_work_types)
        self.tabWidget_work_types_page.setObjectName(u"tabWidget_work_types_page")
        self.tab_work_types_master = QWidget()
        self.tab_work_types_master.setObjectName(u"tab_work_types_master")
        self.layout_tab_work_types_master = QHBoxLayout(self.tab_work_types_master)
        self.layout_tab_work_types_master.setSpacing(16)
        self.layout_tab_work_types_master.setObjectName(u"layout_tab_work_types_master")
        self.layout_tab_work_types_master.setContentsMargins(16, 16, 16, 16)
        self.layout_work_types_left_panel = QVBoxLayout()
        self.layout_work_types_left_panel.setSpacing(10)
        self.layout_work_types_left_panel.setObjectName(u"layout_work_types_left_panel")
        self.layout_work_types_left_panel.setContentsMargins(0, 0, 0, 0)
        self.layout_work_types_row_search = QHBoxLayout()
        self.layout_work_types_row_search.setSpacing(8)
        self.layout_work_types_row_search.setObjectName(u"layout_work_types_row_search")
        self.txt_search_work_types = QLineEdit(self.tab_work_types_master)
        self.txt_search_work_types.setObjectName(u"txt_search_work_types")
        self.txt_search_work_types.setMinimumSize(QSize(280, 36))
        self.txt_search_work_types.setMaximumSize(QSize(16777215, 36))

        self.layout_work_types_row_search.addWidget(self.txt_search_work_types)


        self.layout_work_types_left_panel.addLayout(self.layout_work_types_row_search)

        self.layout_work_types_row_filters = QHBoxLayout()
        self.layout_work_types_row_filters.setSpacing(8)
        self.layout_work_types_row_filters.setObjectName(u"layout_work_types_row_filters")
        self.cmb_filter_work_type_category = QComboBox(self.tab_work_types_master)
        self.cmb_filter_work_type_category.addItem("")
        self.cmb_filter_work_type_category.addItem("")
        self.cmb_filter_work_type_category.addItem("")
        self.cmb_filter_work_type_category.addItem("")
        self.cmb_filter_work_type_category.addItem("")
        self.cmb_filter_work_type_category.addItem("")
        self.cmb_filter_work_type_category.setObjectName(u"cmb_filter_work_type_category")
        self.cmb_filter_work_type_category.setMinimumSize(QSize(160, 46))
        self.cmb_filter_work_type_category.setMaximumSize(QSize(16777215, 16777215))

        self.layout_work_types_row_filters.addWidget(self.cmb_filter_work_type_category)

        self.btn_refresh_work_types = QPushButton(self.tab_work_types_master)
        self.btn_refresh_work_types.setObjectName(u"btn_refresh_work_types")
        self.btn_refresh_work_types.setMinimumSize(QSize(90, 36))
        self.btn_refresh_work_types.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_work_types_row_filters.addWidget(self.btn_refresh_work_types)


        self.layout_work_types_left_panel.addLayout(self.layout_work_types_row_filters)

        self.layout_work_types_row_export = QHBoxLayout()
        self.layout_work_types_row_export.setSpacing(8)
        self.layout_work_types_row_export.setObjectName(u"layout_work_types_row_export")
        self.btn_export_excel_work_types = QPushButton(self.tab_work_types_master)
        self.btn_export_excel_work_types.setObjectName(u"btn_export_excel_work_types")
        self.btn_export_excel_work_types.setMinimumSize(QSize(110, 36))
        self.btn_export_excel_work_types.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_work_types_row_export.addWidget(self.btn_export_excel_work_types)

        self.btn_export_pdf_work_types = QPushButton(self.tab_work_types_master)
        self.btn_export_pdf_work_types.setObjectName(u"btn_export_pdf_work_types")
        self.btn_export_pdf_work_types.setMinimumSize(QSize(100, 36))
        self.btn_export_pdf_work_types.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_work_types_row_export.addWidget(self.btn_export_pdf_work_types)


        self.layout_work_types_left_panel.addLayout(self.layout_work_types_row_export)

        self.layout_work_types_row_actions = QHBoxLayout()
        self.layout_work_types_row_actions.setSpacing(8)
        self.layout_work_types_row_actions.setObjectName(u"layout_work_types_row_actions")
        self.btn_new_work_type = QPushButton(self.tab_work_types_master)
        self.btn_new_work_type.setObjectName(u"btn_new_work_type")
        self.btn_new_work_type.setMinimumSize(QSize(130, 36))
        self.btn_new_work_type.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_work_types_row_actions.addWidget(self.btn_new_work_type)


        self.layout_work_types_left_panel.addLayout(self.layout_work_types_row_actions)

        self.btn_toggle_work_types_table_expanded = QPushButton(self.tab_work_types_master)
        self.btn_toggle_work_types_table_expanded.setObjectName(u"btn_toggle_work_types_table_expanded")
        self.btn_toggle_work_types_table_expanded.setMinimumSize(QSize(0, 34))
        self.btn_toggle_work_types_table_expanded.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle_work_types_table_expanded.setStyleSheet(u"QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; border-radius: 6px; font-size: 12px; font-weight: 600; } QPushButton:hover { background-color: #E1E8F0; }")

        self.layout_work_types_left_panel.addWidget(self.btn_toggle_work_types_table_expanded)

        self.table_work_types = QTableWidget(self.tab_work_types_master)
        if (self.table_work_types.columnCount() < 4):
            self.table_work_types.setColumnCount(4)
        __qtablewidgetitem46 = QTableWidgetItem()
        self.table_work_types.setHorizontalHeaderItem(0, __qtablewidgetitem46)
        __qtablewidgetitem47 = QTableWidgetItem()
        self.table_work_types.setHorizontalHeaderItem(1, __qtablewidgetitem47)
        __qtablewidgetitem48 = QTableWidgetItem()
        self.table_work_types.setHorizontalHeaderItem(2, __qtablewidgetitem48)
        __qtablewidgetitem49 = QTableWidgetItem()
        self.table_work_types.setHorizontalHeaderItem(3, __qtablewidgetitem49)
        self.table_work_types.setObjectName(u"table_work_types")
        self.table_work_types.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_work_types.setAlternatingRowColors(True)
        self.table_work_types.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_work_types.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_work_types.setSortingEnabled(True)
        self.table_work_types.setColumnCount(4)
        self.table_work_types.horizontalHeader().setStretchLastSection(True)

        self.layout_work_types_left_panel.addWidget(self.table_work_types)


        self.layout_tab_work_types_master.addLayout(self.layout_work_types_left_panel)

        self.layout_work_types_right_panel = QVBoxLayout()
        self.layout_work_types_right_panel.setSpacing(0)
        self.layout_work_types_right_panel.setObjectName(u"layout_work_types_right_panel")
        self.layout_work_types_right_panel.setContentsMargins(0, 0, 0, 0)
        self.frame_work_type_card = QFrame(self.tab_work_types_master)
        self.frame_work_type_card.setObjectName(u"frame_work_type_card")
        self.frame_work_type_card.setMaximumSize(QSize(500, 16777215))
        self.layout_work_type_card = QVBoxLayout(self.frame_work_type_card)
        self.layout_work_type_card.setSpacing(0)
        self.layout_work_type_card.setObjectName(u"layout_work_type_card")
        self.layout_work_type_card.setContentsMargins(0, 0, 0, 0)
        self.card_header_work_type = QFrame(self.frame_work_type_card)
        self.card_header_work_type.setObjectName(u"card_header_work_type")
        self.hboxLayout9 = QHBoxLayout(self.card_header_work_type)
        self.hboxLayout9.setObjectName(u"hboxLayout9")
        self.hboxLayout9.setContentsMargins(20, -1, -1, -1)
        self.lbl_work_type_form_title = QLabel(self.card_header_work_type)
        self.lbl_work_type_form_title.setObjectName(u"lbl_work_type_form_title")

        self.hboxLayout9.addWidget(self.lbl_work_type_form_title)

        self.spacerItem13 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout9.addItem(self.spacerItem13)

        self.lbl_work_type_id_display = QLabel(self.card_header_work_type)
        self.lbl_work_type_id_display.setObjectName(u"lbl_work_type_id_display")

        self.hboxLayout9.addWidget(self.lbl_work_type_id_display)


        self.layout_work_type_card.addWidget(self.card_header_work_type)

        self.frame_work_type_body = QFrame(self.frame_work_type_card)
        self.frame_work_type_body.setObjectName(u"frame_work_type_body")
        self.grid_work_type_form = QGridLayout(self.frame_work_type_body)
        self.grid_work_type_form.setObjectName(u"grid_work_type_form")
        self.grid_work_type_form.setHorizontalSpacing(16)
        self.grid_work_type_form.setVerticalSpacing(10)
        self.grid_work_type_form.setContentsMargins(20, 16, 20, 16)
        self.txt_work_type_name = QLineEdit(self.frame_work_type_body)
        self.txt_work_type_name.setObjectName(u"txt_work_type_name")
        self.txt_work_type_name.setMinimumSize(QSize(0, 36))
        self.txt_work_type_name.setMaximumSize(QSize(16777215, 36))

        self.grid_work_type_form.addWidget(self.txt_work_type_name, 4, 0, 1, 1)

        self.lbl_work_type_name = QLabel(self.frame_work_type_body)
        self.lbl_work_type_name.setObjectName(u"lbl_work_type_name")

        self.grid_work_type_form.addWidget(self.lbl_work_type_name, 2, 0, 1, 1)

        self.cmb_work_type_category = QComboBox(self.frame_work_type_body)
        self.cmb_work_type_category.addItem("")
        self.cmb_work_type_category.addItem("")
        self.cmb_work_type_category.addItem("")
        self.cmb_work_type_category.addItem("")
        self.cmb_work_type_category.addItem("")
        self.cmb_work_type_category.setObjectName(u"cmb_work_type_category")
        self.cmb_work_type_category.setMinimumSize(QSize(0, 46))
        self.cmb_work_type_category.setMaximumSize(QSize(16777215, 16777215))

        self.grid_work_type_form.addWidget(self.cmb_work_type_category, 1, 0, 1, 1)

        self.txt_work_type_unit = QLineEdit(self.frame_work_type_body)
        self.txt_work_type_unit.setObjectName(u"txt_work_type_unit")
        self.txt_work_type_unit.setMinimumSize(QSize(0, 36))
        self.txt_work_type_unit.setMaximumSize(QSize(16777215, 36))

        self.grid_work_type_form.addWidget(self.txt_work_type_unit, 6, 0, 1, 1)

        self.lbl_work_type_category = QLabel(self.frame_work_type_body)
        self.lbl_work_type_category.setObjectName(u"lbl_work_type_category")

        self.grid_work_type_form.addWidget(self.lbl_work_type_category, 0, 0, 1, 1)

        self.txt_work_type_id = QLineEdit(self.frame_work_type_body)
        self.txt_work_type_id.setObjectName(u"txt_work_type_id")
        self.txt_work_type_id.setVisible(False)
        self.txt_work_type_id.setReadOnly(True)

        self.grid_work_type_form.addWidget(self.txt_work_type_id, 7, 0, 1, 1)

        self.lbl_work_type_unit = QLabel(self.frame_work_type_body)
        self.lbl_work_type_unit.setObjectName(u"lbl_work_type_unit")

        self.grid_work_type_form.addWidget(self.lbl_work_type_unit, 5, 0, 1, 1)


        self.layout_work_type_card.addWidget(self.frame_work_type_body)

        self.frame_work_type_footer = QFrame(self.frame_work_type_card)
        self.frame_work_type_footer.setObjectName(u"frame_work_type_footer")
        self.hboxLayout10 = QHBoxLayout(self.frame_work_type_footer)
        self.hboxLayout10.setObjectName(u"hboxLayout10")
        self.hboxLayout10.setContentsMargins(20, 12, 20, 12)
        self.spacerItem14 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout10.addItem(self.spacerItem14)

        self.btn_delete_work_type = QPushButton(self.frame_work_type_footer)
        self.btn_delete_work_type.setObjectName(u"btn_delete_work_type")
        self.btn_delete_work_type.setMinimumSize(QSize(90, 36))
        self.btn_delete_work_type.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout10.addWidget(self.btn_delete_work_type)

        self.btn_save_work_type = QPushButton(self.frame_work_type_footer)
        self.btn_save_work_type.setObjectName(u"btn_save_work_type")
        self.btn_save_work_type.setMinimumSize(QSize(110, 36))
        self.btn_save_work_type.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout10.addWidget(self.btn_save_work_type)


        self.layout_work_type_card.addWidget(self.frame_work_type_footer)


        self.layout_work_types_right_panel.addWidget(self.frame_work_type_card)

        self.spacerItem15 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_work_types_right_panel.addItem(self.spacerItem15)


        self.layout_tab_work_types_master.addLayout(self.layout_work_types_right_panel)

        self.tabWidget_work_types_page.addTab(self.tab_work_types_master, "")

        self.layout_work_types_page.addWidget(self.tabWidget_work_types_page)

        self.Pages.addWidget(self.pg_work_types)
        self.pg_receivables = QWidget()
        self.pg_receivables.setObjectName(u"pg_receivables")
        self.layout_receivables_page = QVBoxLayout(self.pg_receivables)
        self.layout_receivables_page.setSpacing(0)
        self.layout_receivables_page.setObjectName(u"layout_receivables_page")
        self.layout_receivables_page.setContentsMargins(0, 0, 0, 0)
        self.tabWidget_receivables = QTabWidget(self.pg_receivables)
        self.tabWidget_receivables.setObjectName(u"tabWidget_receivables")
        self.tab_receivables_dashboard = QWidget()
        self.tab_receivables_dashboard.setObjectName(u"tab_receivables_dashboard")
        self.layout_receivables_dashboard = QVBoxLayout(self.tab_receivables_dashboard)
        self.layout_receivables_dashboard.setSpacing(16)
        self.layout_receivables_dashboard.setObjectName(u"layout_receivables_dashboard")
        self.layout_receivables_dashboard.setContentsMargins(20, 20, 20, 20)
        self.scroll_receivables_dashboard = QScrollArea(self.tab_receivables_dashboard)
        self.scroll_receivables_dashboard.setObjectName(u"scroll_receivables_dashboard")
        self.scroll_receivables_dashboard.setFrameShape(QFrame.NoFrame)
        self.scroll_receivables_dashboard.setWidgetResizable(True)
        self.scroll_receivables_dashboard_contents = QWidget()
        self.scroll_receivables_dashboard_contents.setObjectName(u"scroll_receivables_dashboard_contents")
        self.scroll_receivables_dashboard_contents.setGeometry(QRect(0, 0, 1550, 976))
        self.layout_scroll_receivables_dashboard_contents = QVBoxLayout(self.scroll_receivables_dashboard_contents)
        self.layout_scroll_receivables_dashboard_contents.setSpacing(16)
        self.layout_scroll_receivables_dashboard_contents.setObjectName(u"layout_scroll_receivables_dashboard_contents")
        self.layout_scroll_receivables_dashboard_contents.setContentsMargins(0, 0, 4, 0)
        self.layout_receivables_stats = QHBoxLayout()
        self.layout_receivables_stats.setSpacing(16)
        self.layout_receivables_stats.setObjectName(u"layout_receivables_stats")
        self.card_receivables_total = QFrame(self.scroll_receivables_dashboard_contents)
        self.card_receivables_total.setObjectName(u"card_receivables_total")
        self.card_receivables_total.setMinimumSize(QSize(0, 100))
        self.card_receivables_total.setStyleSheet(u"QFrame#card_receivables_total { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout8 = QVBoxLayout(self.card_receivables_total)
        self.vboxLayout8.setObjectName(u"vboxLayout8")
        self.vboxLayout8.setContentsMargins(18, 14, 18, 14)
        self.lbl_receivables_total_icon = QLabel(self.card_receivables_total)
        self.lbl_receivables_total_icon.setObjectName(u"lbl_receivables_total_icon")

        self.vboxLayout8.addWidget(self.lbl_receivables_total_icon)

        self.lbl_receivables_total_value = QLabel(self.card_receivables_total)
        self.lbl_receivables_total_value.setObjectName(u"lbl_receivables_total_value")

        self.vboxLayout8.addWidget(self.lbl_receivables_total_value)

        self.lbl_receivables_total_label = QLabel(self.card_receivables_total)
        self.lbl_receivables_total_label.setObjectName(u"lbl_receivables_total_label")

        self.vboxLayout8.addWidget(self.lbl_receivables_total_label)


        self.layout_receivables_stats.addWidget(self.card_receivables_total)

        self.card_receivables_month = QFrame(self.scroll_receivables_dashboard_contents)
        self.card_receivables_month.setObjectName(u"card_receivables_month")
        self.card_receivables_month.setMinimumSize(QSize(0, 100))
        self.card_receivables_month.setStyleSheet(u"QFrame#card_receivables_month { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout9 = QVBoxLayout(self.card_receivables_month)
        self.vboxLayout9.setObjectName(u"vboxLayout9")
        self.vboxLayout9.setContentsMargins(18, 14, 18, 14)
        self.lbl_receivables_month_icon = QLabel(self.card_receivables_month)
        self.lbl_receivables_month_icon.setObjectName(u"lbl_receivables_month_icon")

        self.vboxLayout9.addWidget(self.lbl_receivables_month_icon)

        self.lbl_receivables_month_value = QLabel(self.card_receivables_month)
        self.lbl_receivables_month_value.setObjectName(u"lbl_receivables_month_value")

        self.vboxLayout9.addWidget(self.lbl_receivables_month_value)

        self.lbl_receivables_month_label = QLabel(self.card_receivables_month)
        self.lbl_receivables_month_label.setObjectName(u"lbl_receivables_month_label")

        self.vboxLayout9.addWidget(self.lbl_receivables_month_label)


        self.layout_receivables_stats.addWidget(self.card_receivables_month)

        self.card_receivables_open = QFrame(self.scroll_receivables_dashboard_contents)
        self.card_receivables_open.setObjectName(u"card_receivables_open")
        self.card_receivables_open.setMinimumSize(QSize(0, 100))
        self.card_receivables_open.setStyleSheet(u"QFrame#card_receivables_open { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout10 = QVBoxLayout(self.card_receivables_open)
        self.vboxLayout10.setObjectName(u"vboxLayout10")
        self.vboxLayout10.setContentsMargins(18, 14, 18, 14)
        self.lbl_receivables_open_icon = QLabel(self.card_receivables_open)
        self.lbl_receivables_open_icon.setObjectName(u"lbl_receivables_open_icon")

        self.vboxLayout10.addWidget(self.lbl_receivables_open_icon)

        self.lbl_receivables_open_value = QLabel(self.card_receivables_open)
        self.lbl_receivables_open_value.setObjectName(u"lbl_receivables_open_value")

        self.vboxLayout10.addWidget(self.lbl_receivables_open_value)

        self.lbl_receivables_open_label = QLabel(self.card_receivables_open)
        self.lbl_receivables_open_label.setObjectName(u"lbl_receivables_open_label")

        self.vboxLayout10.addWidget(self.lbl_receivables_open_label)


        self.layout_receivables_stats.addWidget(self.card_receivables_open)

        self.card_receivables_overdue = QFrame(self.scroll_receivables_dashboard_contents)
        self.card_receivables_overdue.setObjectName(u"card_receivables_overdue")
        self.card_receivables_overdue.setMinimumSize(QSize(0, 100))
        self.card_receivables_overdue.setStyleSheet(u"QFrame#card_receivables_overdue { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout11 = QVBoxLayout(self.card_receivables_overdue)
        self.vboxLayout11.setObjectName(u"vboxLayout11")
        self.vboxLayout11.setContentsMargins(18, 14, 18, 14)
        self.lbl_receivables_overdue_icon = QLabel(self.card_receivables_overdue)
        self.lbl_receivables_overdue_icon.setObjectName(u"lbl_receivables_overdue_icon")

        self.vboxLayout11.addWidget(self.lbl_receivables_overdue_icon)

        self.lbl_receivables_overdue_value = QLabel(self.card_receivables_overdue)
        self.lbl_receivables_overdue_value.setObjectName(u"lbl_receivables_overdue_value")

        self.vboxLayout11.addWidget(self.lbl_receivables_overdue_value)

        self.lbl_receivables_overdue_label = QLabel(self.card_receivables_overdue)
        self.lbl_receivables_overdue_label.setObjectName(u"lbl_receivables_overdue_label")

        self.vboxLayout11.addWidget(self.lbl_receivables_overdue_label)


        self.layout_receivables_stats.addWidget(self.card_receivables_overdue)


        self.layout_scroll_receivables_dashboard_contents.addLayout(self.layout_receivables_stats)

        self.layout_dashboard_filter = QHBoxLayout()
        self.layout_dashboard_filter.setSpacing(8)
        self.layout_dashboard_filter.setObjectName(u"layout_dashboard_filter")
        self.lbl_dashboard_period = QLabel(self.scroll_receivables_dashboard_contents)
        self.lbl_dashboard_period.setObjectName(u"lbl_dashboard_period")

        self.layout_dashboard_filter.addWidget(self.lbl_dashboard_period)

        self.cmb_dashboard_month = QComboBox(self.scroll_receivables_dashboard_contents)
        self.cmb_dashboard_month.setObjectName(u"cmb_dashboard_month")
        self.cmb_dashboard_month.setMinimumSize(QSize(130, 46))

        self.layout_dashboard_filter.addWidget(self.cmb_dashboard_month)

        self.cmb_dashboard_year = QComboBox(self.scroll_receivables_dashboard_contents)
        self.cmb_dashboard_year.setObjectName(u"cmb_dashboard_year")
        self.cmb_dashboard_year.setMinimumSize(QSize(100, 46))

        self.layout_dashboard_filter.addWidget(self.cmb_dashboard_year)

        self.spacerItem16 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_dashboard_filter.addItem(self.spacerItem16)


        self.layout_scroll_receivables_dashboard_contents.addLayout(self.layout_dashboard_filter)

        self.table_receivables_breakdown = QTableWidget(self.scroll_receivables_dashboard_contents)
        if (self.table_receivables_breakdown.columnCount() < 5):
            self.table_receivables_breakdown.setColumnCount(5)
        __qtablewidgetitem50 = QTableWidgetItem()
        self.table_receivables_breakdown.setHorizontalHeaderItem(0, __qtablewidgetitem50)
        __qtablewidgetitem51 = QTableWidgetItem()
        self.table_receivables_breakdown.setHorizontalHeaderItem(1, __qtablewidgetitem51)
        __qtablewidgetitem52 = QTableWidgetItem()
        self.table_receivables_breakdown.setHorizontalHeaderItem(2, __qtablewidgetitem52)
        __qtablewidgetitem53 = QTableWidgetItem()
        self.table_receivables_breakdown.setHorizontalHeaderItem(3, __qtablewidgetitem53)
        __qtablewidgetitem54 = QTableWidgetItem()
        self.table_receivables_breakdown.setHorizontalHeaderItem(4, __qtablewidgetitem54)
        self.table_receivables_breakdown.setObjectName(u"table_receivables_breakdown")
        self.table_receivables_breakdown.setMinimumSize(QSize(0, 220))
        self.table_receivables_breakdown.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_receivables_breakdown.setAlternatingRowColors(True)
        self.table_receivables_breakdown.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_receivables_breakdown.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_receivables_breakdown.setSortingEnabled(True)
        self.table_receivables_breakdown.setColumnCount(5)
        self.table_receivables_breakdown.horizontalHeader().setStretchLastSection(True)

        self.layout_scroll_receivables_dashboard_contents.addWidget(self.table_receivables_breakdown)

        self.spacerItem17 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_scroll_receivables_dashboard_contents.addItem(self.spacerItem17)

        self.btn_dashboard_record_payment = QPushButton(self.scroll_receivables_dashboard_contents)
        self.btn_dashboard_record_payment.setObjectName(u"btn_dashboard_record_payment")
        self.btn_dashboard_record_payment.setMinimumSize(QSize(0, 40))
        self.btn_dashboard_record_payment.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_dashboard_record_payment.setStyleSheet(u"QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 8px; font-size: 13px; font-weight: 700; } QPushButton:hover { background-color: #1E88E5; }")

        self.layout_scroll_receivables_dashboard_contents.addWidget(self.btn_dashboard_record_payment)

        self.lbl_dashboard_aging_title = QLabel(self.scroll_receivables_dashboard_contents)
        self.lbl_dashboard_aging_title.setObjectName(u"lbl_dashboard_aging_title")
        self.lbl_dashboard_aging_title.setStyleSheet(u"font-size:14px; font-weight:700; color:#1A1F36; background:transparent;")

        self.layout_scroll_receivables_dashboard_contents.addWidget(self.lbl_dashboard_aging_title)

        self.layout_dashboard_aging_row = QHBoxLayout()
        self.layout_dashboard_aging_row.setSpacing(16)
        self.layout_dashboard_aging_row.setObjectName(u"layout_dashboard_aging_row")
        self.card_aging_0_30 = QFrame(self.scroll_receivables_dashboard_contents)
        self.card_aging_0_30.setObjectName(u"card_aging_0_30")
        self.card_aging_0_30.setMinimumSize(QSize(0, 80))
        self.card_aging_0_30.setStyleSheet(u"QFrame#card_aging_0_30 { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout12 = QVBoxLayout(self.card_aging_0_30)
        self.vboxLayout12.setObjectName(u"vboxLayout12")
        self.vboxLayout12.setContentsMargins(16, 12, 16, 12)
        self.lbl_aging_0_30_value = QLabel(self.card_aging_0_30)
        self.lbl_aging_0_30_value.setObjectName(u"lbl_aging_0_30_value")

        self.vboxLayout12.addWidget(self.lbl_aging_0_30_value)

        self.lbl_aging_0_30_label = QLabel(self.card_aging_0_30)
        self.lbl_aging_0_30_label.setObjectName(u"lbl_aging_0_30_label")

        self.vboxLayout12.addWidget(self.lbl_aging_0_30_label)


        self.layout_dashboard_aging_row.addWidget(self.card_aging_0_30)

        self.card_aging_31_60 = QFrame(self.scroll_receivables_dashboard_contents)
        self.card_aging_31_60.setObjectName(u"card_aging_31_60")
        self.card_aging_31_60.setMinimumSize(QSize(0, 80))
        self.card_aging_31_60.setStyleSheet(u"QFrame#card_aging_31_60 { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout13 = QVBoxLayout(self.card_aging_31_60)
        self.vboxLayout13.setObjectName(u"vboxLayout13")
        self.vboxLayout13.setContentsMargins(16, 12, 16, 12)
        self.lbl_aging_31_60_value = QLabel(self.card_aging_31_60)
        self.lbl_aging_31_60_value.setObjectName(u"lbl_aging_31_60_value")

        self.vboxLayout13.addWidget(self.lbl_aging_31_60_value)

        self.lbl_aging_31_60_label = QLabel(self.card_aging_31_60)
        self.lbl_aging_31_60_label.setObjectName(u"lbl_aging_31_60_label")

        self.vboxLayout13.addWidget(self.lbl_aging_31_60_label)


        self.layout_dashboard_aging_row.addWidget(self.card_aging_31_60)

        self.card_aging_61_90 = QFrame(self.scroll_receivables_dashboard_contents)
        self.card_aging_61_90.setObjectName(u"card_aging_61_90")
        self.card_aging_61_90.setMinimumSize(QSize(0, 80))
        self.card_aging_61_90.setStyleSheet(u"QFrame#card_aging_61_90 { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout14 = QVBoxLayout(self.card_aging_61_90)
        self.vboxLayout14.setObjectName(u"vboxLayout14")
        self.vboxLayout14.setContentsMargins(16, 12, 16, 12)
        self.lbl_aging_61_90_value = QLabel(self.card_aging_61_90)
        self.lbl_aging_61_90_value.setObjectName(u"lbl_aging_61_90_value")

        self.vboxLayout14.addWidget(self.lbl_aging_61_90_value)

        self.lbl_aging_61_90_label = QLabel(self.card_aging_61_90)
        self.lbl_aging_61_90_label.setObjectName(u"lbl_aging_61_90_label")

        self.vboxLayout14.addWidget(self.lbl_aging_61_90_label)


        self.layout_dashboard_aging_row.addWidget(self.card_aging_61_90)

        self.card_aging_90_plus = QFrame(self.scroll_receivables_dashboard_contents)
        self.card_aging_90_plus.setObjectName(u"card_aging_90_plus")
        self.card_aging_90_plus.setMinimumSize(QSize(0, 80))
        self.card_aging_90_plus.setStyleSheet(u"QFrame#card_aging_90_plus { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout15 = QVBoxLayout(self.card_aging_90_plus)
        self.vboxLayout15.setObjectName(u"vboxLayout15")
        self.vboxLayout15.setContentsMargins(16, 12, 16, 12)
        self.lbl_aging_90_plus_value = QLabel(self.card_aging_90_plus)
        self.lbl_aging_90_plus_value.setObjectName(u"lbl_aging_90_plus_value")

        self.vboxLayout15.addWidget(self.lbl_aging_90_plus_value)

        self.lbl_aging_90_plus_label = QLabel(self.card_aging_90_plus)
        self.lbl_aging_90_plus_label.setObjectName(u"lbl_aging_90_plus_label")

        self.vboxLayout15.addWidget(self.lbl_aging_90_plus_label)


        self.layout_dashboard_aging_row.addWidget(self.card_aging_90_plus)


        self.layout_scroll_receivables_dashboard_contents.addLayout(self.layout_dashboard_aging_row)

        self.layout_dashboard_bottom_row = QHBoxLayout()
        self.layout_dashboard_bottom_row.setSpacing(16)
        self.layout_dashboard_bottom_row.setObjectName(u"layout_dashboard_bottom_row")
        self.layout_dashboard_chart_col = QVBoxLayout()
        self.layout_dashboard_chart_col.setObjectName(u"layout_dashboard_chart_col")
        self.lbl_dashboard_chart_title = QLabel(self.scroll_receivables_dashboard_contents)
        self.lbl_dashboard_chart_title.setObjectName(u"lbl_dashboard_chart_title")
        self.lbl_dashboard_chart_title.setStyleSheet(u"font-size:14px; font-weight:700; color:#1A1F36; background:transparent;")

        self.layout_dashboard_chart_col.addWidget(self.lbl_dashboard_chart_title)

        self.frame_dashboard_received_chart = QFrame(self.scroll_receivables_dashboard_contents)
        self.frame_dashboard_received_chart.setObjectName(u"frame_dashboard_received_chart")
        self.frame_dashboard_received_chart.setMinimumSize(QSize(0, 180))
        self.frame_dashboard_received_chart.setStyleSheet(u"QFrame#frame_dashboard_received_chart { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.layout_dashboard_received_chart = QHBoxLayout(self.frame_dashboard_received_chart)
        self.layout_dashboard_received_chart.setSpacing(10)
        self.layout_dashboard_received_chart.setObjectName(u"layout_dashboard_received_chart")
        self.layout_dashboard_received_chart.setContentsMargins(16, 16, 16, 12)

        self.layout_dashboard_chart_col.addWidget(self.frame_dashboard_received_chart)

        self.lbl_dashboard_payment_method_title = QLabel(self.scroll_receivables_dashboard_contents)
        self.lbl_dashboard_payment_method_title.setObjectName(u"lbl_dashboard_payment_method_title")
        self.lbl_dashboard_payment_method_title.setStyleSheet(u"font-size:14px; font-weight:700; color:#1A1F36; background:transparent;")

        self.layout_dashboard_chart_col.addWidget(self.lbl_dashboard_payment_method_title)

        self.table_dashboard_payment_methods = QTableWidget(self.scroll_receivables_dashboard_contents)
        if (self.table_dashboard_payment_methods.columnCount() < 2):
            self.table_dashboard_payment_methods.setColumnCount(2)
        __qtablewidgetitem55 = QTableWidgetItem()
        self.table_dashboard_payment_methods.setHorizontalHeaderItem(0, __qtablewidgetitem55)
        __qtablewidgetitem56 = QTableWidgetItem()
        self.table_dashboard_payment_methods.setHorizontalHeaderItem(1, __qtablewidgetitem56)
        self.table_dashboard_payment_methods.setObjectName(u"table_dashboard_payment_methods")
        self.table_dashboard_payment_methods.setMinimumSize(QSize(0, 110))
        self.table_dashboard_payment_methods.setMaximumSize(QSize(16777215, 150))
        self.table_dashboard_payment_methods.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_dashboard_payment_methods.setAlternatingRowColors(True)
        self.table_dashboard_payment_methods.setColumnCount(2)
        self.table_dashboard_payment_methods.horizontalHeader().setStretchLastSection(True)

        self.layout_dashboard_chart_col.addWidget(self.table_dashboard_payment_methods)


        self.layout_dashboard_bottom_row.addLayout(self.layout_dashboard_chart_col)

        self.layout_dashboard_debtors_col = QVBoxLayout()
        self.layout_dashboard_debtors_col.setObjectName(u"layout_dashboard_debtors_col")
        self.lbl_dashboard_debtors_title = QLabel(self.scroll_receivables_dashboard_contents)
        self.lbl_dashboard_debtors_title.setObjectName(u"lbl_dashboard_debtors_title")
        self.lbl_dashboard_debtors_title.setStyleSheet(u"font-size:14px; font-weight:700; color:#1A1F36; background:transparent;")

        self.layout_dashboard_debtors_col.addWidget(self.lbl_dashboard_debtors_title)

        self.table_dashboard_top_debtors = QTableWidget(self.scroll_receivables_dashboard_contents)
        if (self.table_dashboard_top_debtors.columnCount() < 3):
            self.table_dashboard_top_debtors.setColumnCount(3)
        __qtablewidgetitem57 = QTableWidgetItem()
        self.table_dashboard_top_debtors.setHorizontalHeaderItem(0, __qtablewidgetitem57)
        __qtablewidgetitem58 = QTableWidgetItem()
        self.table_dashboard_top_debtors.setHorizontalHeaderItem(1, __qtablewidgetitem58)
        __qtablewidgetitem59 = QTableWidgetItem()
        self.table_dashboard_top_debtors.setHorizontalHeaderItem(2, __qtablewidgetitem59)
        self.table_dashboard_top_debtors.setObjectName(u"table_dashboard_top_debtors")
        self.table_dashboard_top_debtors.setMinimumSize(QSize(0, 200))
        self.table_dashboard_top_debtors.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_dashboard_top_debtors.setAlternatingRowColors(True)
        self.table_dashboard_top_debtors.setColumnCount(3)
        self.table_dashboard_top_debtors.horizontalHeader().setStretchLastSection(True)

        self.layout_dashboard_debtors_col.addWidget(self.table_dashboard_top_debtors)


        self.layout_dashboard_bottom_row.addLayout(self.layout_dashboard_debtors_col)


        self.layout_scroll_receivables_dashboard_contents.addLayout(self.layout_dashboard_bottom_row)

        self.scroll_receivables_dashboard.setWidget(self.scroll_receivables_dashboard_contents)

        self.layout_receivables_dashboard.addWidget(self.scroll_receivables_dashboard)

        self.tabWidget_receivables.addTab(self.tab_receivables_dashboard, "")
        self.tab_receivables_invoices = QWidget()
        self.tab_receivables_invoices.setObjectName(u"tab_receivables_invoices")
        self.layout_receivables_invoices = QVBoxLayout(self.tab_receivables_invoices)
        self.layout_receivables_invoices.setSpacing(12)
        self.layout_receivables_invoices.setObjectName(u"layout_receivables_invoices")
        self.layout_receivables_invoices.setContentsMargins(16, 16, 16, 16)
        self.layout_invoices_toolbar = QHBoxLayout()
        self.layout_invoices_toolbar.setSpacing(8)
        self.layout_invoices_toolbar.setObjectName(u"layout_invoices_toolbar")
        self.cmb_invoice_entity_type = QComboBox(self.tab_receivables_invoices)
        self.cmb_invoice_entity_type.addItem("")
        self.cmb_invoice_entity_type.addItem("")
        self.cmb_invoice_entity_type.addItem("")
        self.cmb_invoice_entity_type.setObjectName(u"cmb_invoice_entity_type")
        self.cmb_invoice_entity_type.setMinimumSize(QSize(150, 46))

        self.layout_invoices_toolbar.addWidget(self.cmb_invoice_entity_type)

        self.cmb_filter_invoice_status = QComboBox(self.tab_receivables_invoices)
        self.cmb_filter_invoice_status.addItem("")
        self.cmb_filter_invoice_status.addItem("")
        self.cmb_filter_invoice_status.addItem("")
        self.cmb_filter_invoice_status.addItem("")
        self.cmb_filter_invoice_status.setObjectName(u"cmb_filter_invoice_status")
        self.cmb_filter_invoice_status.setMinimumSize(QSize(150, 46))
        self.cmb_filter_invoice_status.setMaximumSize(QSize(16777215, 16777215))

        self.layout_invoices_toolbar.addWidget(self.cmb_filter_invoice_status)

        self.btn_refresh_invoices = QPushButton(self.tab_receivables_invoices)
        self.btn_refresh_invoices.setObjectName(u"btn_refresh_invoices")
        self.btn_refresh_invoices.setMinimumSize(QSize(90, 36))
        self.btn_refresh_invoices.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_invoices_toolbar.addWidget(self.btn_refresh_invoices)

        self.btn_export_excel_invoices = QPushButton(self.tab_receivables_invoices)
        self.btn_export_excel_invoices.setObjectName(u"btn_export_excel_invoices")
        self.btn_export_excel_invoices.setMinimumSize(QSize(110, 36))
        self.btn_export_excel_invoices.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_invoices_toolbar.addWidget(self.btn_export_excel_invoices)

        self.btn_export_pdf_invoices = QPushButton(self.tab_receivables_invoices)
        self.btn_export_pdf_invoices.setObjectName(u"btn_export_pdf_invoices")
        self.btn_export_pdf_invoices.setMinimumSize(QSize(100, 36))
        self.btn_export_pdf_invoices.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_invoices_toolbar.addWidget(self.btn_export_pdf_invoices)

        self.spacerItem18 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_invoices_toolbar.addItem(self.spacerItem18)

        self.btn_generate_invoices = QPushButton(self.tab_receivables_invoices)
        self.btn_generate_invoices.setObjectName(u"btn_generate_invoices")
        self.btn_generate_invoices.setMinimumSize(QSize(150, 36))
        self.btn_generate_invoices.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_invoices_toolbar.addWidget(self.btn_generate_invoices)

        self.btn_send_selected_invoices = QPushButton(self.tab_receivables_invoices)
        self.btn_send_selected_invoices.setObjectName(u"btn_send_selected_invoices")
        self.btn_send_selected_invoices.setMinimumSize(QSize(150, 36))
        self.btn_send_selected_invoices.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_invoices_toolbar.addWidget(self.btn_send_selected_invoices)


        self.layout_receivables_invoices.addLayout(self.layout_invoices_toolbar)

        self.table_contractor_invoices = QTableWidget(self.tab_receivables_invoices)
        if (self.table_contractor_invoices.columnCount() < 9):
            self.table_contractor_invoices.setColumnCount(9)
        __qtablewidgetitem60 = QTableWidgetItem()
        self.table_contractor_invoices.setHorizontalHeaderItem(0, __qtablewidgetitem60)
        __qtablewidgetitem61 = QTableWidgetItem()
        self.table_contractor_invoices.setHorizontalHeaderItem(1, __qtablewidgetitem61)
        __qtablewidgetitem62 = QTableWidgetItem()
        self.table_contractor_invoices.setHorizontalHeaderItem(2, __qtablewidgetitem62)
        __qtablewidgetitem63 = QTableWidgetItem()
        self.table_contractor_invoices.setHorizontalHeaderItem(3, __qtablewidgetitem63)
        __qtablewidgetitem64 = QTableWidgetItem()
        self.table_contractor_invoices.setHorizontalHeaderItem(4, __qtablewidgetitem64)
        __qtablewidgetitem65 = QTableWidgetItem()
        self.table_contractor_invoices.setHorizontalHeaderItem(5, __qtablewidgetitem65)
        __qtablewidgetitem66 = QTableWidgetItem()
        self.table_contractor_invoices.setHorizontalHeaderItem(6, __qtablewidgetitem66)
        __qtablewidgetitem67 = QTableWidgetItem()
        self.table_contractor_invoices.setHorizontalHeaderItem(7, __qtablewidgetitem67)
        __qtablewidgetitem68 = QTableWidgetItem()
        self.table_contractor_invoices.setHorizontalHeaderItem(8, __qtablewidgetitem68)
        self.table_contractor_invoices.setObjectName(u"table_contractor_invoices")
        self.table_contractor_invoices.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_contractor_invoices.setAlternatingRowColors(True)
        self.table_contractor_invoices.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_contractor_invoices.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_contractor_invoices.setSortingEnabled(True)
        self.table_contractor_invoices.setColumnCount(9)
        self.table_contractor_invoices.horizontalHeader().setStretchLastSection(True)

        self.layout_receivables_invoices.addWidget(self.table_contractor_invoices)

        self.lbl_invoices_hint = QLabel(self.tab_receivables_invoices)
        self.lbl_invoices_hint.setObjectName(u"lbl_invoices_hint")

        self.layout_receivables_invoices.addWidget(self.lbl_invoices_hint)

        self.tabWidget_receivables.addTab(self.tab_receivables_invoices, "")
        self.tab_expenses_master = QWidget()
        self.tab_expenses_master.setObjectName(u"tab_expenses_master")
        self.layout_tab_expenses_master = QHBoxLayout(self.tab_expenses_master)
        self.layout_tab_expenses_master.setSpacing(16)
        self.layout_tab_expenses_master.setObjectName(u"layout_tab_expenses_master")
        self.layout_tab_expenses_master.setContentsMargins(16, 16, 16, 16)
        self.layout_expenses_left_panel = QVBoxLayout()
        self.layout_expenses_left_panel.setSpacing(10)
        self.layout_expenses_left_panel.setObjectName(u"layout_expenses_left_panel")
        self.layout_expenses_left_panel.setContentsMargins(0, 0, 0, 0)
        self.layout_expenses_row_search = QHBoxLayout()
        self.layout_expenses_row_search.setSpacing(8)
        self.layout_expenses_row_search.setObjectName(u"layout_expenses_row_search")
        self.txt_search_expenses = QLineEdit(self.tab_expenses_master)
        self.txt_search_expenses.setObjectName(u"txt_search_expenses")
        self.txt_search_expenses.setMinimumSize(QSize(280, 36))
        self.txt_search_expenses.setMaximumSize(QSize(16777215, 36))

        self.layout_expenses_row_search.addWidget(self.txt_search_expenses)


        self.layout_expenses_left_panel.addLayout(self.layout_expenses_row_search)

        self.layout_expenses_row_filters = QHBoxLayout()
        self.layout_expenses_row_filters.setSpacing(8)
        self.layout_expenses_row_filters.setObjectName(u"layout_expenses_row_filters")
        self.cmb_filter_expense_category = QComboBox(self.tab_expenses_master)
        self.cmb_filter_expense_category.addItem("")
        self.cmb_filter_expense_category.addItem("")
        self.cmb_filter_expense_category.addItem("")
        self.cmb_filter_expense_category.addItem("")
        self.cmb_filter_expense_category.addItem("")
        self.cmb_filter_expense_category.setObjectName(u"cmb_filter_expense_category")
        self.cmb_filter_expense_category.setMinimumSize(QSize(150, 46))
        self.cmb_filter_expense_category.setMaximumSize(QSize(16777215, 16777215))

        self.layout_expenses_row_filters.addWidget(self.cmb_filter_expense_category)

        self.cmb_filter_expense_contractor = QComboBox(self.tab_expenses_master)
        self.cmb_filter_expense_contractor.setObjectName(u"cmb_filter_expense_contractor")
        self.cmb_filter_expense_contractor.setMinimumSize(QSize(170, 46))
        self.cmb_filter_expense_contractor.setMaximumSize(QSize(16777215, 16777215))

        self.layout_expenses_row_filters.addWidget(self.cmb_filter_expense_contractor)


        self.layout_expenses_left_panel.addLayout(self.layout_expenses_row_filters)

        self.layout_expenses_row_export = QHBoxLayout()
        self.layout_expenses_row_export.setSpacing(8)
        self.layout_expenses_row_export.setObjectName(u"layout_expenses_row_export")
        self.btn_refresh_expenses = QPushButton(self.tab_expenses_master)
        self.btn_refresh_expenses.setObjectName(u"btn_refresh_expenses")
        self.btn_refresh_expenses.setMinimumSize(QSize(90, 36))
        self.btn_refresh_expenses.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_expenses_row_export.addWidget(self.btn_refresh_expenses)

        self.btn_export_excel_expenses = QPushButton(self.tab_expenses_master)
        self.btn_export_excel_expenses.setObjectName(u"btn_export_excel_expenses")
        self.btn_export_excel_expenses.setMinimumSize(QSize(110, 36))
        self.btn_export_excel_expenses.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_expenses_row_export.addWidget(self.btn_export_excel_expenses)

        self.btn_export_pdf_expenses = QPushButton(self.tab_expenses_master)
        self.btn_export_pdf_expenses.setObjectName(u"btn_export_pdf_expenses")
        self.btn_export_pdf_expenses.setMinimumSize(QSize(100, 36))
        self.btn_export_pdf_expenses.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_expenses_row_export.addWidget(self.btn_export_pdf_expenses)


        self.layout_expenses_left_panel.addLayout(self.layout_expenses_row_export)

        self.layout_expenses_row_actions = QHBoxLayout()
        self.layout_expenses_row_actions.setSpacing(8)
        self.layout_expenses_row_actions.setObjectName(u"layout_expenses_row_actions")
        self.btn_new_expense = QPushButton(self.tab_expenses_master)
        self.btn_new_expense.setObjectName(u"btn_new_expense")
        self.btn_new_expense.setMinimumSize(QSize(140, 36))
        self.btn_new_expense.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_expenses_row_actions.addWidget(self.btn_new_expense)


        self.layout_expenses_left_panel.addLayout(self.layout_expenses_row_actions)

        self.btn_toggle_expenses_table_expanded = QPushButton(self.tab_expenses_master)
        self.btn_toggle_expenses_table_expanded.setObjectName(u"btn_toggle_expenses_table_expanded")
        self.btn_toggle_expenses_table_expanded.setMinimumSize(QSize(0, 34))
        self.btn_toggle_expenses_table_expanded.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle_expenses_table_expanded.setStyleSheet(u"QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; border-radius: 6px; font-size: 12px; font-weight: 600; } QPushButton:hover { background-color: #E1E8F0; }")

        self.layout_expenses_left_panel.addWidget(self.btn_toggle_expenses_table_expanded)

        self.table_expenses = QTableWidget(self.tab_expenses_master)
        if (self.table_expenses.columnCount() < 7):
            self.table_expenses.setColumnCount(7)
        __qtablewidgetitem69 = QTableWidgetItem()
        self.table_expenses.setHorizontalHeaderItem(0, __qtablewidgetitem69)
        __qtablewidgetitem70 = QTableWidgetItem()
        self.table_expenses.setHorizontalHeaderItem(1, __qtablewidgetitem70)
        __qtablewidgetitem71 = QTableWidgetItem()
        self.table_expenses.setHorizontalHeaderItem(2, __qtablewidgetitem71)
        __qtablewidgetitem72 = QTableWidgetItem()
        self.table_expenses.setHorizontalHeaderItem(3, __qtablewidgetitem72)
        __qtablewidgetitem73 = QTableWidgetItem()
        self.table_expenses.setHorizontalHeaderItem(4, __qtablewidgetitem73)
        __qtablewidgetitem74 = QTableWidgetItem()
        self.table_expenses.setHorizontalHeaderItem(5, __qtablewidgetitem74)
        __qtablewidgetitem75 = QTableWidgetItem()
        self.table_expenses.setHorizontalHeaderItem(6, __qtablewidgetitem75)
        self.table_expenses.setObjectName(u"table_expenses")
        self.table_expenses.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_expenses.setAlternatingRowColors(True)
        self.table_expenses.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_expenses.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_expenses.setSortingEnabled(True)
        self.table_expenses.setColumnCount(7)
        self.table_expenses.horizontalHeader().setStretchLastSection(True)

        self.layout_expenses_left_panel.addWidget(self.table_expenses)


        self.layout_tab_expenses_master.addLayout(self.layout_expenses_left_panel)

        self.layout_expenses_right_panel = QVBoxLayout()
        self.layout_expenses_right_panel.setSpacing(0)
        self.layout_expenses_right_panel.setObjectName(u"layout_expenses_right_panel")
        self.layout_expenses_right_panel.setContentsMargins(0, 0, 0, 0)
        self.frame_expense_card = QFrame(self.tab_expenses_master)
        self.frame_expense_card.setObjectName(u"frame_expense_card")
        self.frame_expense_card.setMaximumSize(QSize(560, 16777215))
        self.layout_expense_card = QVBoxLayout(self.frame_expense_card)
        self.layout_expense_card.setSpacing(0)
        self.layout_expense_card.setObjectName(u"layout_expense_card")
        self.layout_expense_card.setContentsMargins(0, 0, 0, 0)
        self.card_header_expense = QFrame(self.frame_expense_card)
        self.card_header_expense.setObjectName(u"card_header_expense")
        self.hboxLayout11 = QHBoxLayout(self.card_header_expense)
        self.hboxLayout11.setObjectName(u"hboxLayout11")
        self.hboxLayout11.setContentsMargins(20, -1, -1, -1)
        self.lbl_expense_form_title = QLabel(self.card_header_expense)
        self.lbl_expense_form_title.setObjectName(u"lbl_expense_form_title")

        self.hboxLayout11.addWidget(self.lbl_expense_form_title)

        self.spacerItem19 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout11.addItem(self.spacerItem19)

        self.lbl_expense_id_display = QLabel(self.card_header_expense)
        self.lbl_expense_id_display.setObjectName(u"lbl_expense_id_display")

        self.hboxLayout11.addWidget(self.lbl_expense_id_display)


        self.layout_expense_card.addWidget(self.card_header_expense)

        self.frame_expense_body = QFrame(self.frame_expense_card)
        self.frame_expense_body.setObjectName(u"frame_expense_body")
        self.grid_expense_form = QGridLayout(self.frame_expense_body)
        self.grid_expense_form.setObjectName(u"grid_expense_form")
        self.grid_expense_form.setHorizontalSpacing(16)
        self.grid_expense_form.setVerticalSpacing(10)
        self.grid_expense_form.setContentsMargins(20, 16, 20, 16)
        self.lbl_expense_date = QLabel(self.frame_expense_body)
        self.lbl_expense_date.setObjectName(u"lbl_expense_date")

        self.grid_expense_form.addWidget(self.lbl_expense_date, 0, 0, 1, 1)

        self.lbl_expense_category = QLabel(self.frame_expense_body)
        self.lbl_expense_category.setObjectName(u"lbl_expense_category")

        self.grid_expense_form.addWidget(self.lbl_expense_category, 0, 1, 1, 1)

        self.date_expense = QDateEdit(self.frame_expense_body)
        self.date_expense.setObjectName(u"date_expense")
        self.date_expense.setMinimumSize(QSize(0, 36))
        self.date_expense.setMaximumSize(QSize(16777215, 36))
        self.date_expense.setCalendarPopup(True)

        self.grid_expense_form.addWidget(self.date_expense, 1, 0, 1, 1)

        self.cmb_expense_category = QComboBox(self.frame_expense_body)
        self.cmb_expense_category.addItem("")
        self.cmb_expense_category.addItem("")
        self.cmb_expense_category.addItem("")
        self.cmb_expense_category.addItem("")
        self.cmb_expense_category.setObjectName(u"cmb_expense_category")
        self.cmb_expense_category.setMinimumSize(QSize(0, 46))
        self.cmb_expense_category.setMaximumSize(QSize(16777215, 16777215))

        self.grid_expense_form.addWidget(self.cmb_expense_category, 1, 1, 1, 1)

        self.lbl_expense_description = QLabel(self.frame_expense_body)
        self.lbl_expense_description.setObjectName(u"lbl_expense_description")

        self.grid_expense_form.addWidget(self.lbl_expense_description, 2, 0, 1, 2)

        self.txt_expense_description = QLineEdit(self.frame_expense_body)
        self.txt_expense_description.setObjectName(u"txt_expense_description")
        self.txt_expense_description.setMinimumSize(QSize(0, 36))
        self.txt_expense_description.setMaximumSize(QSize(16777215, 36))

        self.grid_expense_form.addWidget(self.txt_expense_description, 3, 0, 1, 2)

        self.lbl_expense_vendor = QLabel(self.frame_expense_body)
        self.lbl_expense_vendor.setObjectName(u"lbl_expense_vendor")

        self.grid_expense_form.addWidget(self.lbl_expense_vendor, 4, 0, 1, 2)

        self.cmb_expense_vendor = QComboBox(self.frame_expense_body)
        self.cmb_expense_vendor.setObjectName(u"cmb_expense_vendor")
        self.cmb_expense_vendor.setMinimumSize(QSize(0, 46))
        self.cmb_expense_vendor.setMaximumSize(QSize(16777215, 36))
        self.cmb_expense_vendor.setEditable(True)

        self.grid_expense_form.addWidget(self.cmb_expense_vendor, 5, 0, 1, 2)

        self.lbl_expense_amount = QLabel(self.frame_expense_body)
        self.lbl_expense_amount.setObjectName(u"lbl_expense_amount")

        self.grid_expense_form.addWidget(self.lbl_expense_amount, 6, 0, 1, 1)

        self.lbl_expense_submitted_by = QLabel(self.frame_expense_body)
        self.lbl_expense_submitted_by.setObjectName(u"lbl_expense_submitted_by")

        self.grid_expense_form.addWidget(self.lbl_expense_submitted_by, 6, 1, 1, 1)

        self.dspn_expense_amount = QDoubleSpinBox(self.frame_expense_body)
        self.dspn_expense_amount.setObjectName(u"dspn_expense_amount")
        self.dspn_expense_amount.setMinimumSize(QSize(0, 36))
        self.dspn_expense_amount.setMaximumSize(QSize(16777215, 36))
        self.dspn_expense_amount.setDecimals(2)
        self.dspn_expense_amount.setMinimum(0.000000000000000)
        self.dspn_expense_amount.setMaximum(99999.990000000005239)
        self.dspn_expense_amount.setSingleStep(1.000000000000000)
        self.dspn_expense_amount.setProperty(u"groupSeparatorShown", True)

        self.grid_expense_form.addWidget(self.dspn_expense_amount, 7, 0, 1, 1)

        self.cmb_expense_submitted_by = QComboBox(self.frame_expense_body)
        self.cmb_expense_submitted_by.addItem("")
        self.cmb_expense_submitted_by.addItem("")
        self.cmb_expense_submitted_by.setObjectName(u"cmb_expense_submitted_by")
        self.cmb_expense_submitted_by.setMinimumSize(QSize(0, 46))
        self.cmb_expense_submitted_by.setMaximumSize(QSize(16777215, 36))

        self.grid_expense_form.addWidget(self.cmb_expense_submitted_by, 7, 1, 1, 1)

        self.lbl_expense_entity_type = QLabel(self.frame_expense_body)
        self.lbl_expense_entity_type.setObjectName(u"lbl_expense_entity_type")

        self.grid_expense_form.addWidget(self.lbl_expense_entity_type, 8, 0, 1, 1)

        self.lbl_expense_contractor = QLabel(self.frame_expense_body)
        self.lbl_expense_contractor.setObjectName(u"lbl_expense_contractor")

        self.grid_expense_form.addWidget(self.lbl_expense_contractor, 8, 1, 1, 1)

        self.cmb_expense_entity_type = QComboBox(self.frame_expense_body)
        self.cmb_expense_entity_type.addItem("")
        self.cmb_expense_entity_type.addItem("")
        self.cmb_expense_entity_type.addItem("")
        self.cmb_expense_entity_type.addItem("")
        self.cmb_expense_entity_type.setObjectName(u"cmb_expense_entity_type")
        self.cmb_expense_entity_type.setMinimumSize(QSize(0, 46))
        self.cmb_expense_entity_type.setMaximumSize(QSize(16777215, 36))

        self.grid_expense_form.addWidget(self.cmb_expense_entity_type, 9, 0, 1, 1)

        self.cmb_expense_contractor = QComboBox(self.frame_expense_body)
        self.cmb_expense_contractor.setObjectName(u"cmb_expense_contractor")
        self.cmb_expense_contractor.setMinimumSize(QSize(0, 46))
        self.cmb_expense_contractor.setMaximumSize(QSize(16777215, 36))
        self.cmb_expense_contractor.setEditable(True)

        self.grid_expense_form.addWidget(self.cmb_expense_contractor, 9, 1, 1, 1)

        self.lbl_expense_receipt = QLabel(self.frame_expense_body)
        self.lbl_expense_receipt.setObjectName(u"lbl_expense_receipt")

        self.grid_expense_form.addWidget(self.lbl_expense_receipt, 10, 0, 1, 2)

        self.txt_expense_receipt_path = QLineEdit(self.frame_expense_body)
        self.txt_expense_receipt_path.setObjectName(u"txt_expense_receipt_path")
        self.txt_expense_receipt_path.setMinimumSize(QSize(0, 36))
        self.txt_expense_receipt_path.setMaximumSize(QSize(16777215, 36))
        self.txt_expense_receipt_path.setReadOnly(True)

        self.grid_expense_form.addWidget(self.txt_expense_receipt_path, 11, 0, 1, 1)

        self.btn_expense_attach_receipt = QPushButton(self.frame_expense_body)
        self.btn_expense_attach_receipt.setObjectName(u"btn_expense_attach_receipt")
        self.btn_expense_attach_receipt.setMinimumSize(QSize(0, 36))
        self.btn_expense_attach_receipt.setMaximumSize(QSize(16777215, 36))
        self.btn_expense_attach_receipt.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.grid_expense_form.addWidget(self.btn_expense_attach_receipt, 11, 1, 1, 1)

        self.txt_expense_id = QLineEdit(self.frame_expense_body)
        self.txt_expense_id.setObjectName(u"txt_expense_id")
        self.txt_expense_id.setVisible(False)
        self.txt_expense_id.setReadOnly(True)

        self.grid_expense_form.addWidget(self.txt_expense_id, 12, 0, 1, 1)


        self.layout_expense_card.addWidget(self.frame_expense_body)

        self.frame_expense_footer = QFrame(self.frame_expense_card)
        self.frame_expense_footer.setObjectName(u"frame_expense_footer")
        self.hboxLayout12 = QHBoxLayout(self.frame_expense_footer)
        self.hboxLayout12.setObjectName(u"hboxLayout12")
        self.hboxLayout12.setContentsMargins(20, 12, 20, 12)
        self.spacerItem20 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout12.addItem(self.spacerItem20)

        self.btn_delete_expense = QPushButton(self.frame_expense_footer)
        self.btn_delete_expense.setObjectName(u"btn_delete_expense")
        self.btn_delete_expense.setMinimumSize(QSize(90, 36))
        self.btn_delete_expense.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout12.addWidget(self.btn_delete_expense)

        self.btn_save_expense = QPushButton(self.frame_expense_footer)
        self.btn_save_expense.setObjectName(u"btn_save_expense")
        self.btn_save_expense.setMinimumSize(QSize(110, 36))
        self.btn_save_expense.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout12.addWidget(self.btn_save_expense)


        self.layout_expense_card.addWidget(self.frame_expense_footer)


        self.layout_expenses_right_panel.addWidget(self.frame_expense_card)

        self.spacerItem21 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_expenses_right_panel.addItem(self.spacerItem21)


        self.layout_tab_expenses_master.addLayout(self.layout_expenses_right_panel)

        self.tabWidget_receivables.addTab(self.tab_expenses_master, "")
        self.tab_pnl = QWidget()
        self.tab_pnl.setObjectName(u"tab_pnl")
        self.layout_tab_pnl = QVBoxLayout(self.tab_pnl)
        self.layout_tab_pnl.setObjectName(u"layout_tab_pnl")
        self.layout_tab_pnl.setContentsMargins(16, 16, 16, 16)
        self.layout_pnl_filter = QHBoxLayout()
        self.layout_pnl_filter.setObjectName(u"layout_pnl_filter")
        self.lbl_pnl_period = QLabel(self.tab_pnl)
        self.lbl_pnl_period.setObjectName(u"lbl_pnl_period")

        self.layout_pnl_filter.addWidget(self.lbl_pnl_period)

        self.cmb_pnl_month = QComboBox(self.tab_pnl)
        self.cmb_pnl_month.setObjectName(u"cmb_pnl_month")
        self.cmb_pnl_month.setMinimumSize(QSize(140, 46))

        self.layout_pnl_filter.addWidget(self.cmb_pnl_month)

        self.cmb_pnl_year = QComboBox(self.tab_pnl)
        self.cmb_pnl_year.setObjectName(u"cmb_pnl_year")
        self.cmb_pnl_year.setMinimumSize(QSize(100, 46))

        self.layout_pnl_filter.addWidget(self.cmb_pnl_year)

        self.btn_export_pdf_pnl = QPushButton(self.tab_pnl)
        self.btn_export_pdf_pnl.setObjectName(u"btn_export_pdf_pnl")
        self.btn_export_pdf_pnl.setMinimumSize(QSize(0, 36))
        self.btn_export_pdf_pnl.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_pnl_filter.addWidget(self.btn_export_pdf_pnl)

        self.spacerItem22 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_pnl_filter.addItem(self.spacerItem22)


        self.layout_tab_pnl.addLayout(self.layout_pnl_filter)

        self.card_pnl_revenue = QFrame(self.tab_pnl)
        self.card_pnl_revenue.setObjectName(u"card_pnl_revenue")
        self.card_pnl_revenue.setMinimumSize(QSize(0, 90))
        self.card_pnl_revenue.setStyleSheet(u"QFrame#card_pnl_revenue { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout16 = QVBoxLayout(self.card_pnl_revenue)
        self.vboxLayout16.setObjectName(u"vboxLayout16")
        self.vboxLayout16.setContentsMargins(18, 12, 18, 12)
        self.lbl_pnl_revenue_value = QLabel(self.card_pnl_revenue)
        self.lbl_pnl_revenue_value.setObjectName(u"lbl_pnl_revenue_value")

        self.vboxLayout16.addWidget(self.lbl_pnl_revenue_value)

        self.lbl_pnl_revenue_label = QLabel(self.card_pnl_revenue)
        self.lbl_pnl_revenue_label.setObjectName(u"lbl_pnl_revenue_label")

        self.vboxLayout16.addWidget(self.lbl_pnl_revenue_label)


        self.layout_tab_pnl.addWidget(self.card_pnl_revenue)

        self.lbl_pnl_expenses_title = QLabel(self.tab_pnl)
        self.lbl_pnl_expenses_title.setObjectName(u"lbl_pnl_expenses_title")
        self.lbl_pnl_expenses_title.setStyleSheet(u"font-size:14px; font-weight:700; color:#1A1F36; background:transparent;")

        self.layout_tab_pnl.addWidget(self.lbl_pnl_expenses_title)

        self.table_pnl_expenses = QTableWidget(self.tab_pnl)
        if (self.table_pnl_expenses.columnCount() < 2):
            self.table_pnl_expenses.setColumnCount(2)
        __qtablewidgetitem76 = QTableWidgetItem()
        self.table_pnl_expenses.setHorizontalHeaderItem(0, __qtablewidgetitem76)
        __qtablewidgetitem77 = QTableWidgetItem()
        self.table_pnl_expenses.setHorizontalHeaderItem(1, __qtablewidgetitem77)
        self.table_pnl_expenses.setObjectName(u"table_pnl_expenses")
        self.table_pnl_expenses.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_pnl_expenses.setAlternatingRowColors(True)
        self.table_pnl_expenses.setColumnCount(2)
        self.table_pnl_expenses.horizontalHeader().setStretchLastSection(True)

        self.layout_tab_pnl.addWidget(self.table_pnl_expenses)

        self.card_pnl_summary = QFrame(self.tab_pnl)
        self.card_pnl_summary.setObjectName(u"card_pnl_summary")
        self.card_pnl_summary.setMinimumSize(QSize(0, 110))
        self.card_pnl_summary.setStyleSheet(u"QFrame#card_pnl_summary { background-color:#F8FAFD; border:1px solid #E3E8EE; border-radius:12px; }")
        self.vboxLayout17 = QVBoxLayout(self.card_pnl_summary)
        self.vboxLayout17.setObjectName(u"vboxLayout17")
        self.vboxLayout17.setContentsMargins(18, 12, 18, 12)
        self.lbl_pnl_total_expenses_value = QLabel(self.card_pnl_summary)
        self.lbl_pnl_total_expenses_value.setObjectName(u"lbl_pnl_total_expenses_value")

        self.vboxLayout17.addWidget(self.lbl_pnl_total_expenses_value)

        self.lbl_pnl_net_profit_value = QLabel(self.card_pnl_summary)
        self.lbl_pnl_net_profit_value.setObjectName(u"lbl_pnl_net_profit_value")

        self.vboxLayout17.addWidget(self.lbl_pnl_net_profit_value)


        self.layout_tab_pnl.addWidget(self.card_pnl_summary)

        self.tabWidget_receivables.addTab(self.tab_pnl, "")
        self.tab_1099 = QWidget()
        self.tab_1099.setObjectName(u"tab_1099")
        self.layout_tab_1099 = QVBoxLayout(self.tab_1099)
        self.layout_tab_1099.setObjectName(u"layout_tab_1099")
        self.layout_tab_1099.setContentsMargins(16, 16, 16, 16)
        self.layout_1099_filter = QHBoxLayout()
        self.layout_1099_filter.setObjectName(u"layout_1099_filter")
        self.lbl_1099_year = QLabel(self.tab_1099)
        self.lbl_1099_year.setObjectName(u"lbl_1099_year")

        self.layout_1099_filter.addWidget(self.lbl_1099_year)

        self.cmb_1099_year = QComboBox(self.tab_1099)
        self.cmb_1099_year.setObjectName(u"cmb_1099_year")
        self.cmb_1099_year.setMinimumSize(QSize(100, 46))

        self.layout_1099_filter.addWidget(self.cmb_1099_year)

        self.btn_export_pdf_1099 = QPushButton(self.tab_1099)
        self.btn_export_pdf_1099.setObjectName(u"btn_export_pdf_1099")
        self.btn_export_pdf_1099.setMinimumSize(QSize(0, 36))
        self.btn_export_pdf_1099.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_1099_filter.addWidget(self.btn_export_pdf_1099)

        self.btn_export_excel_1099 = QPushButton(self.tab_1099)
        self.btn_export_excel_1099.setObjectName(u"btn_export_excel_1099")
        self.btn_export_excel_1099.setMinimumSize(QSize(0, 36))
        self.btn_export_excel_1099.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_1099_filter.addWidget(self.btn_export_excel_1099)

        self.spacerItem23 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_1099_filter.addItem(self.spacerItem23)


        self.layout_tab_1099.addLayout(self.layout_1099_filter)

        self.lbl_1099_note = QLabel(self.tab_1099)
        self.lbl_1099_note.setObjectName(u"lbl_1099_note")
        self.lbl_1099_note.setStyleSheet(u"font-size:12px; color:#6B7C93; background:transparent;")
        self.lbl_1099_note.setWordWrap(True)

        self.layout_tab_1099.addWidget(self.lbl_1099_note)

        self.table_1099 = QTableWidget(self.tab_1099)
        if (self.table_1099.columnCount() < 5):
            self.table_1099.setColumnCount(5)
        __qtablewidgetitem78 = QTableWidgetItem()
        self.table_1099.setHorizontalHeaderItem(0, __qtablewidgetitem78)
        __qtablewidgetitem79 = QTableWidgetItem()
        self.table_1099.setHorizontalHeaderItem(1, __qtablewidgetitem79)
        __qtablewidgetitem80 = QTableWidgetItem()
        self.table_1099.setHorizontalHeaderItem(2, __qtablewidgetitem80)
        __qtablewidgetitem81 = QTableWidgetItem()
        self.table_1099.setHorizontalHeaderItem(3, __qtablewidgetitem81)
        __qtablewidgetitem82 = QTableWidgetItem()
        self.table_1099.setHorizontalHeaderItem(4, __qtablewidgetitem82)
        self.table_1099.setObjectName(u"table_1099")
        self.table_1099.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_1099.setAlternatingRowColors(True)
        self.table_1099.setColumnCount(5)
        self.table_1099.horizontalHeader().setStretchLastSection(True)

        self.layout_tab_1099.addWidget(self.table_1099)

        self.lbl_1099_summary = QLabel(self.tab_1099)
        self.lbl_1099_summary.setObjectName(u"lbl_1099_summary")
        self.lbl_1099_summary.setStyleSheet(u"font-size:13px; font-weight:700; color:#1565C0; background:transparent;")

        self.layout_tab_1099.addWidget(self.lbl_1099_summary)

        self.tabWidget_receivables.addTab(self.tab_1099, "")
        self.tab_sales_summary = QWidget()
        self.tab_sales_summary.setObjectName(u"tab_sales_summary")
        self.layout_tab_sales_summary = QVBoxLayout(self.tab_sales_summary)
        self.layout_tab_sales_summary.setObjectName(u"layout_tab_sales_summary")
        self.layout_tab_sales_summary.setContentsMargins(16, 16, 16, 16)
        self.layout_sales_summary_filter = QHBoxLayout()
        self.layout_sales_summary_filter.setObjectName(u"layout_sales_summary_filter")
        self.lbl_sales_summary_period = QLabel(self.tab_sales_summary)
        self.lbl_sales_summary_period.setObjectName(u"lbl_sales_summary_period")

        self.layout_sales_summary_filter.addWidget(self.lbl_sales_summary_period)

        self.cmb_sales_summary_month = QComboBox(self.tab_sales_summary)
        self.cmb_sales_summary_month.setObjectName(u"cmb_sales_summary_month")
        self.cmb_sales_summary_month.setMinimumSize(QSize(140, 46))

        self.layout_sales_summary_filter.addWidget(self.cmb_sales_summary_month)

        self.cmb_sales_summary_year = QComboBox(self.tab_sales_summary)
        self.cmb_sales_summary_year.setObjectName(u"cmb_sales_summary_year")
        self.cmb_sales_summary_year.setMinimumSize(QSize(100, 46))

        self.layout_sales_summary_filter.addWidget(self.cmb_sales_summary_year)

        self.lbl_sales_summary_type = QLabel(self.tab_sales_summary)
        self.lbl_sales_summary_type.setObjectName(u"lbl_sales_summary_type")

        self.layout_sales_summary_filter.addWidget(self.lbl_sales_summary_type)

        self.cmb_sales_summary_type = QComboBox(self.tab_sales_summary)
        self.cmb_sales_summary_type.addItem("")
        self.cmb_sales_summary_type.addItem("")
        self.cmb_sales_summary_type.addItem("")
        self.cmb_sales_summary_type.addItem("")
        self.cmb_sales_summary_type.setObjectName(u"cmb_sales_summary_type")
        self.cmb_sales_summary_type.setMinimumSize(QSize(130, 46))

        self.layout_sales_summary_filter.addWidget(self.cmb_sales_summary_type)

        self.btn_export_pdf_sales_summary = QPushButton(self.tab_sales_summary)
        self.btn_export_pdf_sales_summary.setObjectName(u"btn_export_pdf_sales_summary")
        self.btn_export_pdf_sales_summary.setMinimumSize(QSize(0, 36))
        self.btn_export_pdf_sales_summary.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_sales_summary_filter.addWidget(self.btn_export_pdf_sales_summary)

        self.spacerItem24 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_sales_summary_filter.addItem(self.spacerItem24)


        self.layout_tab_sales_summary.addLayout(self.layout_sales_summary_filter)

        self.table_sales_summary = QTableWidget(self.tab_sales_summary)
        if (self.table_sales_summary.columnCount() < 6):
            self.table_sales_summary.setColumnCount(6)
        __qtablewidgetitem83 = QTableWidgetItem()
        self.table_sales_summary.setHorizontalHeaderItem(0, __qtablewidgetitem83)
        __qtablewidgetitem84 = QTableWidgetItem()
        self.table_sales_summary.setHorizontalHeaderItem(1, __qtablewidgetitem84)
        __qtablewidgetitem85 = QTableWidgetItem()
        self.table_sales_summary.setHorizontalHeaderItem(2, __qtablewidgetitem85)
        __qtablewidgetitem86 = QTableWidgetItem()
        self.table_sales_summary.setHorizontalHeaderItem(3, __qtablewidgetitem86)
        __qtablewidgetitem87 = QTableWidgetItem()
        self.table_sales_summary.setHorizontalHeaderItem(4, __qtablewidgetitem87)
        __qtablewidgetitem88 = QTableWidgetItem()
        self.table_sales_summary.setHorizontalHeaderItem(5, __qtablewidgetitem88)
        self.table_sales_summary.setObjectName(u"table_sales_summary")
        self.table_sales_summary.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_sales_summary.setAlternatingRowColors(True)
        self.table_sales_summary.setSortingEnabled(True)
        self.table_sales_summary.setColumnCount(6)
        self.table_sales_summary.horizontalHeader().setStretchLastSection(True)

        self.layout_tab_sales_summary.addWidget(self.table_sales_summary)

        self.lbl_sales_summary_total = QLabel(self.tab_sales_summary)
        self.lbl_sales_summary_total.setObjectName(u"lbl_sales_summary_total")
        self.lbl_sales_summary_total.setStyleSheet(u"font-size:14px; font-weight:700; color:#1565C0; background:transparent;")

        self.layout_tab_sales_summary.addWidget(self.lbl_sales_summary_total)

        self.tabWidget_receivables.addTab(self.tab_sales_summary, "")

        self.layout_receivables_page.addWidget(self.tabWidget_receivables)

        self.Pages.addWidget(self.pg_receivables)
        self.pg_customer = QWidget()
        self.pg_customer.setObjectName(u"pg_customer")
        self.layout_customer_page = QHBoxLayout(self.pg_customer)
        self.layout_customer_page.setSpacing(16)
        self.layout_customer_page.setObjectName(u"layout_customer_page")
        self.layout_customer_page.setContentsMargins(16, 16, 16, 16)
        self.layout_customers_left_panel = QVBoxLayout()
        self.layout_customers_left_panel.setSpacing(10)
        self.layout_customers_left_panel.setObjectName(u"layout_customers_left_panel")
        self.layout_customers_left_panel.setContentsMargins(0, 0, 0, 0)
        self.layout_customers_row_search = QHBoxLayout()
        self.layout_customers_row_search.setObjectName(u"layout_customers_row_search")
        self.txt_search_customers = QLineEdit(self.pg_customer)
        self.txt_search_customers.setObjectName(u"txt_search_customers")
        self.txt_search_customers.setMinimumSize(QSize(0, 36))

        self.layout_customers_row_search.addWidget(self.txt_search_customers)


        self.layout_customers_left_panel.addLayout(self.layout_customers_row_search)

        self.layout_customers_row_export = QHBoxLayout()
        self.layout_customers_row_export.setSpacing(8)
        self.layout_customers_row_export.setObjectName(u"layout_customers_row_export")
        self.btn_refresh_customers = QPushButton(self.pg_customer)
        self.btn_refresh_customers.setObjectName(u"btn_refresh_customers")
        self.btn_refresh_customers.setMinimumSize(QSize(0, 36))
        self.btn_refresh_customers.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_customers_row_export.addWidget(self.btn_refresh_customers)

        self.btn_export_excel_customers = QPushButton(self.pg_customer)
        self.btn_export_excel_customers.setObjectName(u"btn_export_excel_customers")
        self.btn_export_excel_customers.setMinimumSize(QSize(0, 36))
        self.btn_export_excel_customers.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_customers_row_export.addWidget(self.btn_export_excel_customers)

        self.btn_export_pdf_customers = QPushButton(self.pg_customer)
        self.btn_export_pdf_customers.setObjectName(u"btn_export_pdf_customers")
        self.btn_export_pdf_customers.setMinimumSize(QSize(0, 36))
        self.btn_export_pdf_customers.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_customers_row_export.addWidget(self.btn_export_pdf_customers)


        self.layout_customers_left_panel.addLayout(self.layout_customers_row_export)

        self.btn_new_customer = QPushButton(self.pg_customer)
        self.btn_new_customer.setObjectName(u"btn_new_customer")
        self.btn_new_customer.setMinimumSize(QSize(0, 36))
        self.btn_new_customer.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_customers_left_panel.addWidget(self.btn_new_customer)

        self.btn_toggle_customers_table_expanded = QPushButton(self.pg_customer)
        self.btn_toggle_customers_table_expanded.setObjectName(u"btn_toggle_customers_table_expanded")
        self.btn_toggle_customers_table_expanded.setMinimumSize(QSize(0, 34))
        self.btn_toggle_customers_table_expanded.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle_customers_table_expanded.setStyleSheet(u"QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; border-radius: 6px; font-size: 12px; font-weight: 600; } QPushButton:hover { background-color: #E1E8F0; }")

        self.layout_customers_left_panel.addWidget(self.btn_toggle_customers_table_expanded)

        self.table_customers = QTableWidget(self.pg_customer)
        if (self.table_customers.columnCount() < 6):
            self.table_customers.setColumnCount(6)
        __qtablewidgetitem89 = QTableWidgetItem()
        self.table_customers.setHorizontalHeaderItem(0, __qtablewidgetitem89)
        __qtablewidgetitem90 = QTableWidgetItem()
        self.table_customers.setHorizontalHeaderItem(1, __qtablewidgetitem90)
        __qtablewidgetitem91 = QTableWidgetItem()
        self.table_customers.setHorizontalHeaderItem(2, __qtablewidgetitem91)
        __qtablewidgetitem92 = QTableWidgetItem()
        self.table_customers.setHorizontalHeaderItem(3, __qtablewidgetitem92)
        __qtablewidgetitem93 = QTableWidgetItem()
        self.table_customers.setHorizontalHeaderItem(4, __qtablewidgetitem93)
        __qtablewidgetitem94 = QTableWidgetItem()
        self.table_customers.setHorizontalHeaderItem(5, __qtablewidgetitem94)
        self.table_customers.setObjectName(u"table_customers")
        self.table_customers.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_customers.setAlternatingRowColors(True)
        self.table_customers.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_customers.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_customers.setSortingEnabled(True)
        self.table_customers.setColumnCount(6)
        self.table_customers.horizontalHeader().setStretchLastSection(True)

        self.layout_customers_left_panel.addWidget(self.table_customers)


        self.layout_customer_page.addLayout(self.layout_customers_left_panel)

        self.layout_customers_right_panel = QVBoxLayout()
        self.layout_customers_right_panel.setSpacing(0)
        self.layout_customers_right_panel.setObjectName(u"layout_customers_right_panel")
        self.layout_customers_right_panel.setContentsMargins(0, 0, 0, 0)
        self.scroll_customer_form = QScrollArea(self.pg_customer)
        self.scroll_customer_form.setObjectName(u"scroll_customer_form")
        self.scroll_customer_form.setFrameShape(QFrame.NoFrame)
        self.scroll_customer_form.setWidgetResizable(True)
        self.scroll_customer_form_contents = QWidget()
        self.scroll_customer_form_contents.setObjectName(u"scroll_customer_form_contents")
        self.scroll_customer_form_contents.setGeometry(QRect(0, 0, 1088, 958))
        self.layout_scroll_customer_form_contents = QVBoxLayout(self.scroll_customer_form_contents)
        self.layout_scroll_customer_form_contents.setObjectName(u"layout_scroll_customer_form_contents")
        self.frame_customer_card = QFrame(self.scroll_customer_form_contents)
        self.frame_customer_card.setObjectName(u"frame_customer_card")
        self.layout_customer_card = QVBoxLayout(self.frame_customer_card)
        self.layout_customer_card.setSpacing(0)
        self.layout_customer_card.setObjectName(u"layout_customer_card")
        self.layout_customer_card.setContentsMargins(0, 0, 0, 0)
        self.card_header_customer = QFrame(self.frame_customer_card)
        self.card_header_customer.setObjectName(u"card_header_customer")
        self.hboxLayout13 = QHBoxLayout(self.card_header_customer)
        self.hboxLayout13.setObjectName(u"hboxLayout13")
        self.hboxLayout13.setContentsMargins(20, -1, -1, -1)
        self.lbl_customer_form_title = QLabel(self.card_header_customer)
        self.lbl_customer_form_title.setObjectName(u"lbl_customer_form_title")

        self.hboxLayout13.addWidget(self.lbl_customer_form_title)

        self.spacerItem25 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout13.addItem(self.spacerItem25)

        self.lbl_customer_id_display = QLabel(self.card_header_customer)
        self.lbl_customer_id_display.setObjectName(u"lbl_customer_id_display")

        self.hboxLayout13.addWidget(self.lbl_customer_id_display)


        self.layout_customer_card.addWidget(self.card_header_customer)

        self.frame_customer_body = QFrame(self.frame_customer_card)
        self.frame_customer_body.setObjectName(u"frame_customer_body")
        self.grid_customer_form = QGridLayout(self.frame_customer_body)
        self.grid_customer_form.setObjectName(u"grid_customer_form")
        self.grid_customer_form.setHorizontalSpacing(16)
        self.grid_customer_form.setVerticalSpacing(10)
        self.grid_customer_form.setContentsMargins(20, 16, 20, 16)
        self.txt_customer_zip = QLineEdit(self.frame_customer_body)
        self.txt_customer_zip.setObjectName(u"txt_customer_zip")
        self.txt_customer_zip.setMinimumSize(QSize(0, 36))

        self.grid_customer_form.addWidget(self.txt_customer_zip, 9, 2, 1, 1)

        self.txt_customer_id = QLineEdit(self.frame_customer_body)
        self.txt_customer_id.setObjectName(u"txt_customer_id")
        self.txt_customer_id.setVisible(False)
        self.txt_customer_id.setReadOnly(True)

        self.grid_customer_form.addWidget(self.txt_customer_id, 12, 0, 1, 1)

        self.lbl_customer_city = QLabel(self.frame_customer_body)
        self.lbl_customer_city.setObjectName(u"lbl_customer_city")

        self.grid_customer_form.addWidget(self.lbl_customer_city, 8, 1, 1, 1)

        self.cmb_customer_state = QComboBox(self.frame_customer_body)
        self.cmb_customer_state.setObjectName(u"cmb_customer_state")
        self.cmb_customer_state.setMinimumSize(QSize(0, 46))

        self.grid_customer_form.addWidget(self.cmb_customer_state, 9, 0, 1, 1)

        self.cmb_customer_city = QComboBox(self.frame_customer_body)
        self.cmb_customer_city.setObjectName(u"cmb_customer_city")
        self.cmb_customer_city.setMinimumSize(QSize(0, 46))

        self.grid_customer_form.addWidget(self.cmb_customer_city, 9, 1, 1, 1)

        self.txt_customer_address2 = QLineEdit(self.frame_customer_body)
        self.txt_customer_address2.setObjectName(u"txt_customer_address2")
        self.txt_customer_address2.setMinimumSize(QSize(0, 36))

        self.grid_customer_form.addWidget(self.txt_customer_address2, 7, 1, 1, 1)

        self.txt_customer_address = QLineEdit(self.frame_customer_body)
        self.txt_customer_address.setObjectName(u"txt_customer_address")
        self.txt_customer_address.setMinimumSize(QSize(0, 36))

        self.grid_customer_form.addWidget(self.txt_customer_address, 7, 0, 1, 1)

        self.lbl_customer_state = QLabel(self.frame_customer_body)
        self.lbl_customer_state.setObjectName(u"lbl_customer_state")

        self.grid_customer_form.addWidget(self.lbl_customer_state, 8, 0, 1, 1)

        self.lbl_customer_address = QLabel(self.frame_customer_body)
        self.lbl_customer_address.setObjectName(u"lbl_customer_address")

        self.grid_customer_form.addWidget(self.lbl_customer_address, 6, 0, 1, 2)

        self.lbl_customer_name = QLabel(self.frame_customer_body)
        self.lbl_customer_name.setObjectName(u"lbl_customer_name")

        self.grid_customer_form.addWidget(self.lbl_customer_name, 0, 0, 1, 2)

        self.lbl_customer_email = QLabel(self.frame_customer_body)
        self.lbl_customer_email.setObjectName(u"lbl_customer_email")

        self.grid_customer_form.addWidget(self.lbl_customer_email, 2, 0, 1, 1)

        self.txt_customer_name = QLineEdit(self.frame_customer_body)
        self.txt_customer_name.setObjectName(u"txt_customer_name")
        self.txt_customer_name.setMinimumSize(QSize(0, 36))

        self.grid_customer_form.addWidget(self.txt_customer_name, 1, 0, 1, 2)

        self.txt_customer_email = QLineEdit(self.frame_customer_body)
        self.txt_customer_email.setObjectName(u"txt_customer_email")
        self.txt_customer_email.setMinimumSize(QSize(0, 36))

        self.grid_customer_form.addWidget(self.txt_customer_email, 3, 0, 1, 1)

        self.lbl_customer_phone = QLabel(self.frame_customer_body)
        self.lbl_customer_phone.setObjectName(u"lbl_customer_phone")

        self.grid_customer_form.addWidget(self.lbl_customer_phone, 2, 1, 1, 1)

        self.txt_customer_phone = QLineEdit(self.frame_customer_body)
        self.txt_customer_phone.setObjectName(u"txt_customer_phone")
        self.txt_customer_phone.setMinimumSize(QSize(0, 36))

        self.grid_customer_form.addWidget(self.txt_customer_phone, 3, 1, 1, 1)

        self.lbl_customer_zip = QLabel(self.frame_customer_body)
        self.lbl_customer_zip.setObjectName(u"lbl_customer_zip")

        self.grid_customer_form.addWidget(self.lbl_customer_zip, 8, 2, 1, 1)

        self.txt_customer_phone2 = QLineEdit(self.frame_customer_body)
        self.txt_customer_phone2.setObjectName(u"txt_customer_phone2")
        self.txt_customer_phone2.setMinimumSize(QSize(0, 36))

        self.grid_customer_form.addWidget(self.txt_customer_phone2, 3, 2, 1, 1)

        self.lbl_customer_phone2 = QLabel(self.frame_customer_body)
        self.lbl_customer_phone2.setObjectName(u"lbl_customer_phone2")

        self.grid_customer_form.addWidget(self.lbl_customer_phone2, 2, 2, 1, 1)


        self.layout_customer_card.addWidget(self.frame_customer_body)

        self.frame_customer_job_history = QFrame(self.frame_customer_card)
        self.frame_customer_job_history.setObjectName(u"frame_customer_job_history")
        self.layout_customer_job_history = QVBoxLayout(self.frame_customer_job_history)
        self.layout_customer_job_history.setObjectName(u"layout_customer_job_history")
        self.layout_customer_job_history.setContentsMargins(20, 10, 20, 10)
        self.lbl_customer_job_history_title = QLabel(self.frame_customer_job_history)
        self.lbl_customer_job_history_title.setObjectName(u"lbl_customer_job_history_title")
        self.lbl_customer_job_history_title.setStyleSheet(u"font-size:13px; font-weight:700; color:#37474F; background:transparent;")

        self.layout_customer_job_history.addWidget(self.lbl_customer_job_history_title)

        self.table_customer_job_history = QTableWidget(self.frame_customer_job_history)
        if (self.table_customer_job_history.columnCount() < 6):
            self.table_customer_job_history.setColumnCount(6)
        __qtablewidgetitem95 = QTableWidgetItem()
        self.table_customer_job_history.setHorizontalHeaderItem(0, __qtablewidgetitem95)
        __qtablewidgetitem96 = QTableWidgetItem()
        self.table_customer_job_history.setHorizontalHeaderItem(1, __qtablewidgetitem96)
        __qtablewidgetitem97 = QTableWidgetItem()
        self.table_customer_job_history.setHorizontalHeaderItem(2, __qtablewidgetitem97)
        __qtablewidgetitem98 = QTableWidgetItem()
        self.table_customer_job_history.setHorizontalHeaderItem(3, __qtablewidgetitem98)
        __qtablewidgetitem99 = QTableWidgetItem()
        self.table_customer_job_history.setHorizontalHeaderItem(4, __qtablewidgetitem99)
        __qtablewidgetitem100 = QTableWidgetItem()
        self.table_customer_job_history.setHorizontalHeaderItem(5, __qtablewidgetitem100)
        self.table_customer_job_history.setObjectName(u"table_customer_job_history")
        self.table_customer_job_history.setMinimumSize(QSize(0, 160))
        self.table_customer_job_history.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_customer_job_history.setAlternatingRowColors(True)
        self.table_customer_job_history.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_customer_job_history.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_customer_job_history.setColumnCount(6)
        self.table_customer_job_history.horizontalHeader().setStretchLastSection(True)

        self.layout_customer_job_history.addWidget(self.table_customer_job_history)

        self.lbl_customer_job_history_total = QLabel(self.frame_customer_job_history)
        self.lbl_customer_job_history_total.setObjectName(u"lbl_customer_job_history_total")
        self.lbl_customer_job_history_total.setStyleSheet(u"font-size:13px; font-weight:700; color:#1565C0; background:transparent;")

        self.layout_customer_job_history.addWidget(self.lbl_customer_job_history_total)


        self.layout_customer_card.addWidget(self.frame_customer_job_history)

        self.frame_customer_footer = QFrame(self.frame_customer_card)
        self.frame_customer_footer.setObjectName(u"frame_customer_footer")
        self.hboxLayout14 = QHBoxLayout(self.frame_customer_footer)
        self.hboxLayout14.setObjectName(u"hboxLayout14")
        self.hboxLayout14.setContentsMargins(20, 12, 20, 12)
        self.spacerItem26 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout14.addItem(self.spacerItem26)

        self.btn_delete_customer = QPushButton(self.frame_customer_footer)
        self.btn_delete_customer.setObjectName(u"btn_delete_customer")
        self.btn_delete_customer.setMinimumSize(QSize(90, 36))
        self.btn_delete_customer.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout14.addWidget(self.btn_delete_customer)

        self.btn_save_customer = QPushButton(self.frame_customer_footer)
        self.btn_save_customer.setObjectName(u"btn_save_customer")
        self.btn_save_customer.setMinimumSize(QSize(110, 36))
        self.btn_save_customer.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout14.addWidget(self.btn_save_customer)


        self.layout_customer_card.addWidget(self.frame_customer_footer)


        self.layout_scroll_customer_form_contents.addWidget(self.frame_customer_card)

        self.spacerItem27 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_scroll_customer_form_contents.addItem(self.spacerItem27)

        self.scroll_customer_form.setWidget(self.scroll_customer_form_contents)

        self.layout_customers_right_panel.addWidget(self.scroll_customer_form)


        self.layout_customer_page.addLayout(self.layout_customers_right_panel)

        self.Pages.addWidget(self.pg_customer)
        self.pg_user = QWidget()
        self.pg_user.setObjectName(u"pg_user")
        self.layout_user_page = QVBoxLayout(self.pg_user)
        self.layout_user_page.setSpacing(0)
        self.layout_user_page.setObjectName(u"layout_user_page")
        self.layout_user_page.setContentsMargins(0, 0, 0, 0)
        self.tabWidget_user = QTabWidget(self.pg_user)
        self.tabWidget_user.setObjectName(u"tabWidget_user")
        self.tab_users_master = QWidget()
        self.tab_users_master.setObjectName(u"tab_users_master")
        self.layout_tab_users_master = QHBoxLayout(self.tab_users_master)
        self.layout_tab_users_master.setSpacing(16)
        self.layout_tab_users_master.setObjectName(u"layout_tab_users_master")
        self.layout_tab_users_master.setContentsMargins(16, 16, 16, 16)
        self.layout_users_left_panel = QVBoxLayout()
        self.layout_users_left_panel.setSpacing(10)
        self.layout_users_left_panel.setObjectName(u"layout_users_left_panel")
        self.layout_users_left_panel.setContentsMargins(0, 0, 0, 0)
        self.layout_users_row_search = QHBoxLayout()
        self.layout_users_row_search.setSpacing(8)
        self.layout_users_row_search.setObjectName(u"layout_users_row_search")
        self.txt_search_users = QLineEdit(self.tab_users_master)
        self.txt_search_users.setObjectName(u"txt_search_users")
        self.txt_search_users.setMinimumSize(QSize(280, 36))

        self.layout_users_row_search.addWidget(self.txt_search_users)


        self.layout_users_left_panel.addLayout(self.layout_users_row_search)

        self.layout_users_row_filters = QHBoxLayout()
        self.layout_users_row_filters.setSpacing(8)
        self.layout_users_row_filters.setObjectName(u"layout_users_row_filters")
        self.cmb_filter_user_status = QComboBox(self.tab_users_master)
        self.cmb_filter_user_status.addItem("")
        self.cmb_filter_user_status.addItem("")
        self.cmb_filter_user_status.addItem("")
        self.cmb_filter_user_status.addItem("")
        self.cmb_filter_user_status.setObjectName(u"cmb_filter_user_status")
        self.cmb_filter_user_status.setMinimumSize(QSize(140, 46))
        self.cmb_filter_user_status.setMaximumSize(QSize(16777215, 16777215))

        self.layout_users_row_filters.addWidget(self.cmb_filter_user_status)

        self.btn_refresh_users = QPushButton(self.tab_users_master)
        self.btn_refresh_users.setObjectName(u"btn_refresh_users")
        self.btn_refresh_users.setMinimumSize(QSize(90, 36))
        self.btn_refresh_users.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_users_row_filters.addWidget(self.btn_refresh_users)


        self.layout_users_left_panel.addLayout(self.layout_users_row_filters)

        self.layout_users_row_export = QHBoxLayout()
        self.layout_users_row_export.setSpacing(8)
        self.layout_users_row_export.setObjectName(u"layout_users_row_export")
        self.btn_export_excel_users = QPushButton(self.tab_users_master)
        self.btn_export_excel_users.setObjectName(u"btn_export_excel_users")
        self.btn_export_excel_users.setMinimumSize(QSize(110, 36))
        self.btn_export_excel_users.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_users_row_export.addWidget(self.btn_export_excel_users)

        self.btn_export_pdf_users = QPushButton(self.tab_users_master)
        self.btn_export_pdf_users.setObjectName(u"btn_export_pdf_users")
        self.btn_export_pdf_users.setMinimumSize(QSize(100, 36))
        self.btn_export_pdf_users.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_users_row_export.addWidget(self.btn_export_pdf_users)


        self.layout_users_left_panel.addLayout(self.layout_users_row_export)

        self.layout_users_row_actions = QHBoxLayout()
        self.layout_users_row_actions.setSpacing(8)
        self.layout_users_row_actions.setObjectName(u"layout_users_row_actions")
        self.btn_update_user = QPushButton(self.tab_users_master)
        self.btn_update_user.setObjectName(u"btn_update_user")
        self.btn_update_user.setMinimumSize(QSize(110, 36))
        self.btn_update_user.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_users_row_actions.addWidget(self.btn_update_user)

        self.btn_new_user = QPushButton(self.tab_users_master)
        self.btn_new_user.setObjectName(u"btn_new_user")
        self.btn_new_user.setMinimumSize(QSize(110, 36))
        self.btn_new_user.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_users_row_actions.addWidget(self.btn_new_user)


        self.layout_users_left_panel.addLayout(self.layout_users_row_actions)

        self.btn_toggle_users_table_expanded = QPushButton(self.tab_users_master)
        self.btn_toggle_users_table_expanded.setObjectName(u"btn_toggle_users_table_expanded")
        self.btn_toggle_users_table_expanded.setMinimumSize(QSize(0, 34))
        self.btn_toggle_users_table_expanded.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle_users_table_expanded.setStyleSheet(u"QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; border-radius: 6px; font-size: 12px; font-weight: 600; } QPushButton:hover { background-color: #E1E8F0; }")

        self.layout_users_left_panel.addWidget(self.btn_toggle_users_table_expanded)

        self.table_users = QTableWidget(self.tab_users_master)
        if (self.table_users.columnCount() < 9):
            self.table_users.setColumnCount(9)
        __qtablewidgetitem101 = QTableWidgetItem()
        self.table_users.setHorizontalHeaderItem(0, __qtablewidgetitem101)
        __qtablewidgetitem102 = QTableWidgetItem()
        self.table_users.setHorizontalHeaderItem(1, __qtablewidgetitem102)
        __qtablewidgetitem103 = QTableWidgetItem()
        self.table_users.setHorizontalHeaderItem(2, __qtablewidgetitem103)
        __qtablewidgetitem104 = QTableWidgetItem()
        self.table_users.setHorizontalHeaderItem(3, __qtablewidgetitem104)
        __qtablewidgetitem105 = QTableWidgetItem()
        self.table_users.setHorizontalHeaderItem(4, __qtablewidgetitem105)
        __qtablewidgetitem106 = QTableWidgetItem()
        self.table_users.setHorizontalHeaderItem(5, __qtablewidgetitem106)
        __qtablewidgetitem107 = QTableWidgetItem()
        self.table_users.setHorizontalHeaderItem(6, __qtablewidgetitem107)
        __qtablewidgetitem108 = QTableWidgetItem()
        self.table_users.setHorizontalHeaderItem(7, __qtablewidgetitem108)
        __qtablewidgetitem109 = QTableWidgetItem()
        self.table_users.setHorizontalHeaderItem(8, __qtablewidgetitem109)
        self.table_users.setObjectName(u"table_users")
        self.table_users.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_users.setAlternatingRowColors(True)
        self.table_users.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_users.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_users.setSortingEnabled(True)
        self.table_users.setColumnCount(9)
        self.table_users.horizontalHeader().setStretchLastSection(True)

        self.layout_users_left_panel.addWidget(self.table_users)


        self.layout_tab_users_master.addLayout(self.layout_users_left_panel)

        self.layout_users_right_panel = QVBoxLayout()
        self.layout_users_right_panel.setSpacing(0)
        self.layout_users_right_panel.setObjectName(u"layout_users_right_panel")
        self.layout_users_right_panel.setContentsMargins(0, 0, 0, 0)
        self.frame_user_card = QFrame(self.tab_users_master)
        self.frame_user_card.setObjectName(u"frame_user_card")
        self.frame_user_card.setMaximumSize(QSize(860, 16777215))
        self.layout_user_card = QVBoxLayout(self.frame_user_card)
        self.layout_user_card.setSpacing(0)
        self.layout_user_card.setObjectName(u"layout_user_card")
        self.layout_user_card.setContentsMargins(0, 0, 0, 0)
        self.card_header_user = QFrame(self.frame_user_card)
        self.card_header_user.setObjectName(u"card_header_user")
        self.hboxLayout15 = QHBoxLayout(self.card_header_user)
        self.hboxLayout15.setObjectName(u"hboxLayout15")
        self.hboxLayout15.setContentsMargins(20, -1, -1, -1)
        self.lbl_user_form_title = QLabel(self.card_header_user)
        self.lbl_user_form_title.setObjectName(u"lbl_user_form_title")

        self.hboxLayout15.addWidget(self.lbl_user_form_title)

        self.spacerItem28 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout15.addItem(self.spacerItem28)

        self.lbl_user_id_display = QLabel(self.card_header_user)
        self.lbl_user_id_display.setObjectName(u"lbl_user_id_display")

        self.hboxLayout15.addWidget(self.lbl_user_id_display)


        self.layout_user_card.addWidget(self.card_header_user)

        self.frame_user_body = QFrame(self.frame_user_card)
        self.frame_user_body.setObjectName(u"frame_user_body")
        self.grid_user_form = QGridLayout(self.frame_user_body)
        self.grid_user_form.setObjectName(u"grid_user_form")
        self.grid_user_form.setHorizontalSpacing(16)
        self.grid_user_form.setVerticalSpacing(10)
        self.grid_user_form.setContentsMargins(20, 16, 20, 16)
        self.lbl_user_full_name = QLabel(self.frame_user_body)
        self.lbl_user_full_name.setObjectName(u"lbl_user_full_name")

        self.grid_user_form.addWidget(self.lbl_user_full_name, 0, 0, 1, 2)

        self.lbl_user_username = QLabel(self.frame_user_body)
        self.lbl_user_username.setObjectName(u"lbl_user_username")

        self.grid_user_form.addWidget(self.lbl_user_username, 0, 2, 1, 1)

        self.txt_user_full_name = QLineEdit(self.frame_user_body)
        self.txt_user_full_name.setObjectName(u"txt_user_full_name")
        self.txt_user_full_name.setMinimumSize(QSize(0, 36))
        self.txt_user_full_name.setMaximumSize(QSize(16777215, 36))

        self.grid_user_form.addWidget(self.txt_user_full_name, 1, 0, 1, 2)

        self.txt_user_username = QLineEdit(self.frame_user_body)
        self.txt_user_username.setObjectName(u"txt_user_username")
        self.txt_user_username.setMinimumSize(QSize(0, 36))
        self.txt_user_username.setMaximumSize(QSize(16777215, 36))

        self.grid_user_form.addWidget(self.txt_user_username, 1, 2, 1, 1)

        self.lbl_user_email = QLabel(self.frame_user_body)
        self.lbl_user_email.setObjectName(u"lbl_user_email")

        self.grid_user_form.addWidget(self.lbl_user_email, 2, 0, 1, 1)

        self.lbl_user_phone = QLabel(self.frame_user_body)
        self.lbl_user_phone.setObjectName(u"lbl_user_phone")

        self.grid_user_form.addWidget(self.lbl_user_phone, 2, 1, 1, 1)

        self.lbl_user_phone2 = QLabel(self.frame_user_body)
        self.lbl_user_phone2.setObjectName(u"lbl_user_phone2")

        self.grid_user_form.addWidget(self.lbl_user_phone2, 2, 2, 1, 1)

        self.txt_user_email = QLineEdit(self.frame_user_body)
        self.txt_user_email.setObjectName(u"txt_user_email")
        self.txt_user_email.setMinimumSize(QSize(0, 36))
        self.txt_user_email.setMaximumSize(QSize(16777215, 36))

        self.grid_user_form.addWidget(self.txt_user_email, 3, 0, 1, 1)

        self.txt_user_phone = QLineEdit(self.frame_user_body)
        self.txt_user_phone.setObjectName(u"txt_user_phone")
        self.txt_user_phone.setMinimumSize(QSize(0, 36))
        self.txt_user_phone.setMaximumSize(QSize(16777215, 36))

        self.grid_user_form.addWidget(self.txt_user_phone, 3, 1, 1, 1)

        self.txt_user_phone2 = QLineEdit(self.frame_user_body)
        self.txt_user_phone2.setObjectName(u"txt_user_phone2")
        self.txt_user_phone2.setMinimumSize(QSize(0, 36))
        self.txt_user_phone2.setMaximumSize(QSize(16777215, 36))

        self.grid_user_form.addWidget(self.txt_user_phone2, 3, 2, 1, 1)

        self.div_user_1 = QFrame(self.frame_user_body)
        self.div_user_1.setObjectName(u"div_user_1")
        self.div_user_1.setMaximumSize(QSize(16777215, 1))

        self.grid_user_form.addWidget(self.div_user_1, 4, 0, 1, 3)

        self.lbl_user_password = QLabel(self.frame_user_body)
        self.lbl_user_password.setObjectName(u"lbl_user_password")

        self.grid_user_form.addWidget(self.lbl_user_password, 5, 0, 1, 2)

        self.lbl_user_confirm_password = QLabel(self.frame_user_body)
        self.lbl_user_confirm_password.setObjectName(u"lbl_user_confirm_password")

        self.grid_user_form.addWidget(self.lbl_user_confirm_password, 5, 2, 1, 1)

        self.txt_user_password = QLineEdit(self.frame_user_body)
        self.txt_user_password.setObjectName(u"txt_user_password")
        self.txt_user_password.setMinimumSize(QSize(0, 36))
        self.txt_user_password.setMaximumSize(QSize(16777215, 36))
        self.txt_user_password.setEchoMode(QLineEdit.Password)

        self.grid_user_form.addWidget(self.txt_user_password, 6, 0, 1, 2)

        self.txt_user_confirm_password = QLineEdit(self.frame_user_body)
        self.txt_user_confirm_password.setObjectName(u"txt_user_confirm_password")
        self.txt_user_confirm_password.setMinimumSize(QSize(0, 36))
        self.txt_user_confirm_password.setMaximumSize(QSize(16777215, 36))
        self.txt_user_confirm_password.setEchoMode(QLineEdit.Password)

        self.grid_user_form.addWidget(self.txt_user_confirm_password, 6, 2, 1, 1)

        self.div_user_2 = QFrame(self.frame_user_body)
        self.div_user_2.setObjectName(u"div_user_2")
        self.div_user_2.setMaximumSize(QSize(16777215, 1))

        self.grid_user_form.addWidget(self.div_user_2, 7, 0, 1, 3)

        self.lbl_user_role = QLabel(self.frame_user_body)
        self.lbl_user_role.setObjectName(u"lbl_user_role")

        self.grid_user_form.addWidget(self.lbl_user_role, 8, 0, 1, 1)

        self.lbl_user_status = QLabel(self.frame_user_body)
        self.lbl_user_status.setObjectName(u"lbl_user_status")

        self.grid_user_form.addWidget(self.lbl_user_status, 8, 1, 1, 1)

        self.cmb_user_role = QComboBox(self.frame_user_body)
        self.cmb_user_role.addItem("")
        self.cmb_user_role.addItem("")
        self.cmb_user_role.addItem("")
        self.cmb_user_role.setObjectName(u"cmb_user_role")
        self.cmb_user_role.setMinimumSize(QSize(0, 46))
        self.cmb_user_role.setMaximumSize(QSize(16777215, 16777215))

        self.grid_user_form.addWidget(self.cmb_user_role, 9, 0, 1, 1)

        self.cmb_user_status = QComboBox(self.frame_user_body)
        self.cmb_user_status.addItem("")
        self.cmb_user_status.addItem("")
        self.cmb_user_status.addItem("")
        self.cmb_user_status.setObjectName(u"cmb_user_status")
        self.cmb_user_status.setMinimumSize(QSize(0, 46))
        self.cmb_user_status.setMaximumSize(QSize(16777215, 16777215))

        self.grid_user_form.addWidget(self.cmb_user_status, 9, 1, 1, 1)

        self.div_user_3 = QFrame(self.frame_user_body)
        self.div_user_3.setObjectName(u"div_user_3")
        self.div_user_3.setMaximumSize(QSize(16777215, 1))

        self.grid_user_form.addWidget(self.div_user_3, 10, 0, 1, 3)

        self.lbl_user_last_login = QLabel(self.frame_user_body)
        self.lbl_user_last_login.setObjectName(u"lbl_user_last_login")

        self.grid_user_form.addWidget(self.lbl_user_last_login, 11, 0, 1, 1)

        self.lbl_user_created_at = QLabel(self.frame_user_body)
        self.lbl_user_created_at.setObjectName(u"lbl_user_created_at")

        self.grid_user_form.addWidget(self.lbl_user_created_at, 11, 2, 1, 1)

        self.txt_user_last_login = QLineEdit(self.frame_user_body)
        self.txt_user_last_login.setObjectName(u"txt_user_last_login")
        self.txt_user_last_login.setMinimumSize(QSize(0, 36))
        self.txt_user_last_login.setMaximumSize(QSize(16777215, 36))
        self.txt_user_last_login.setReadOnly(True)

        self.grid_user_form.addWidget(self.txt_user_last_login, 12, 0, 1, 1)

        self.txt_user_created_at = QLineEdit(self.frame_user_body)
        self.txt_user_created_at.setObjectName(u"txt_user_created_at")
        self.txt_user_created_at.setMinimumSize(QSize(0, 36))
        self.txt_user_created_at.setMaximumSize(QSize(16777215, 36))
        self.txt_user_created_at.setReadOnly(True)

        self.grid_user_form.addWidget(self.txt_user_created_at, 12, 2, 1, 1)

        self.txt_user_id = QLineEdit(self.frame_user_body)
        self.txt_user_id.setObjectName(u"txt_user_id")
        self.txt_user_id.setMinimumSize(QSize(0, 36))
        self.txt_user_id.setMaximumSize(QSize(16777215, 36))
        self.txt_user_id.setVisible(False)
        self.txt_user_id.setReadOnly(True)

        self.grid_user_form.addWidget(self.txt_user_id, 13, 0, 1, 1)


        self.layout_user_card.addWidget(self.frame_user_body)

        self.frame_user_footer = QFrame(self.frame_user_card)
        self.frame_user_footer.setObjectName(u"frame_user_footer")
        self.hboxLayout16 = QHBoxLayout(self.frame_user_footer)
        self.hboxLayout16.setObjectName(u"hboxLayout16")
        self.hboxLayout16.setContentsMargins(20, 12, 20, 12)
        self.spacerItem29 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout16.addItem(self.spacerItem29)

        self.btn_delete_user = QPushButton(self.frame_user_footer)
        self.btn_delete_user.setObjectName(u"btn_delete_user")
        self.btn_delete_user.setMinimumSize(QSize(90, 36))
        self.btn_delete_user.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout16.addWidget(self.btn_delete_user)

        self.btn_save_user = QPushButton(self.frame_user_footer)
        self.btn_save_user.setObjectName(u"btn_save_user")
        self.btn_save_user.setMinimumSize(QSize(110, 36))
        self.btn_save_user.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout16.addWidget(self.btn_save_user)


        self.layout_user_card.addWidget(self.frame_user_footer)


        self.layout_users_right_panel.addWidget(self.frame_user_card)

        self.spacerItem30 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_users_right_panel.addItem(self.spacerItem30)


        self.layout_tab_users_master.addLayout(self.layout_users_right_panel)

        self.tabWidget_user.addTab(self.tab_users_master, "")

        self.layout_user_page.addWidget(self.tabWidget_user)

        self.Pages.addWidget(self.pg_user)
        self.pg_products = QWidget()
        self.pg_products.setObjectName(u"pg_products")
        self.layout_products_page = QVBoxLayout(self.pg_products)
        self.layout_products_page.setSpacing(0)
        self.layout_products_page.setObjectName(u"layout_products_page")
        self.layout_products_page.setContentsMargins(0, 0, 0, 0)
        self.tabWidget_products_page = QTabWidget(self.pg_products)
        self.tabWidget_products_page.setObjectName(u"tabWidget_products_page")
        self.tab_products_list = QWidget()
        self.tab_products_list.setObjectName(u"tab_products_list")
        self.layout_tab_products_list = QVBoxLayout(self.tab_products_list)
        self.layout_tab_products_list.setSpacing(12)
        self.layout_tab_products_list.setObjectName(u"layout_tab_products_list")
        self.layout_tab_products_list.setContentsMargins(16, 16, 16, 16)
        self.layout_products_toolbar = QHBoxLayout()
        self.layout_products_toolbar.setSpacing(8)
        self.layout_products_toolbar.setObjectName(u"layout_products_toolbar")
        self.txt_search_products = QLineEdit(self.tab_products_list)
        self.txt_search_products.setObjectName(u"txt_search_products")
        self.txt_search_products.setMinimumSize(QSize(280, 36))
        self.txt_search_products.setMaximumSize(QSize(16777215, 36))

        self.layout_products_toolbar.addWidget(self.txt_search_products)

        self.btn_refresh_products = QPushButton(self.tab_products_list)
        self.btn_refresh_products.setObjectName(u"btn_refresh_products")
        self.btn_refresh_products.setMinimumSize(QSize(90, 36))
        self.btn_refresh_products.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_products_toolbar.addWidget(self.btn_refresh_products)

        self.btn_export_excel_products = QPushButton(self.tab_products_list)
        self.btn_export_excel_products.setObjectName(u"btn_export_excel_products")
        self.btn_export_excel_products.setMinimumSize(QSize(110, 36))
        self.btn_export_excel_products.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_products_toolbar.addWidget(self.btn_export_excel_products)

        self.btn_export_pdf_products = QPushButton(self.tab_products_list)
        self.btn_export_pdf_products.setObjectName(u"btn_export_pdf_products")
        self.btn_export_pdf_products.setMinimumSize(QSize(100, 36))
        self.btn_export_pdf_products.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_products_toolbar.addWidget(self.btn_export_pdf_products)

        self.spacerItem31 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_products_toolbar.addItem(self.spacerItem31)

        self.btn_new_product = QPushButton(self.tab_products_list)
        self.btn_new_product.setObjectName(u"btn_new_product")
        self.btn_new_product.setMinimumSize(QSize(130, 36))
        self.btn_new_product.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_products_toolbar.addWidget(self.btn_new_product)


        self.layout_tab_products_list.addLayout(self.layout_products_toolbar)

        self.table_products = QTableWidget(self.tab_products_list)
        if (self.table_products.columnCount() < 6):
            self.table_products.setColumnCount(6)
        __qtablewidgetitem110 = QTableWidgetItem()
        self.table_products.setHorizontalHeaderItem(0, __qtablewidgetitem110)
        __qtablewidgetitem111 = QTableWidgetItem()
        self.table_products.setHorizontalHeaderItem(1, __qtablewidgetitem111)
        __qtablewidgetitem112 = QTableWidgetItem()
        self.table_products.setHorizontalHeaderItem(2, __qtablewidgetitem112)
        __qtablewidgetitem113 = QTableWidgetItem()
        self.table_products.setHorizontalHeaderItem(3, __qtablewidgetitem113)
        __qtablewidgetitem114 = QTableWidgetItem()
        self.table_products.setHorizontalHeaderItem(4, __qtablewidgetitem114)
        __qtablewidgetitem115 = QTableWidgetItem()
        self.table_products.setHorizontalHeaderItem(5, __qtablewidgetitem115)
        self.table_products.setObjectName(u"table_products")
        self.table_products.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_products.setAlternatingRowColors(True)
        self.table_products.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_products.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_products.setSortingEnabled(True)
        self.table_products.setColumnCount(6)
        self.table_products.horizontalHeader().setStretchLastSection(True)

        self.layout_tab_products_list.addWidget(self.table_products)

        self.tabWidget_products_page.addTab(self.tab_products_list, "")
        self.tab_product_form = QWidget()
        self.tab_product_form.setObjectName(u"tab_product_form")
        self.layout_tab_product_form = QVBoxLayout(self.tab_product_form)
        self.layout_tab_product_form.setSpacing(0)
        self.layout_tab_product_form.setObjectName(u"layout_tab_product_form")
        self.layout_tab_product_form.setContentsMargins(20, 20, 20, 20)
        self.frame_product_card = QFrame(self.tab_product_form)
        self.frame_product_card.setObjectName(u"frame_product_card")
        self.frame_product_card.setMaximumSize(QSize(560, 16777215))
        self.layout_product_card = QVBoxLayout(self.frame_product_card)
        self.layout_product_card.setSpacing(0)
        self.layout_product_card.setObjectName(u"layout_product_card")
        self.layout_product_card.setContentsMargins(0, 0, 0, 0)
        self.card_header_product = QFrame(self.frame_product_card)
        self.card_header_product.setObjectName(u"card_header_product")
        self.hboxLayout17 = QHBoxLayout(self.card_header_product)
        self.hboxLayout17.setObjectName(u"hboxLayout17")
        self.hboxLayout17.setContentsMargins(20, -1, -1, -1)
        self.lbl_product_form_title = QLabel(self.card_header_product)
        self.lbl_product_form_title.setObjectName(u"lbl_product_form_title")

        self.hboxLayout17.addWidget(self.lbl_product_form_title)

        self.spacerItem32 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout17.addItem(self.spacerItem32)

        self.lbl_product_id_display = QLabel(self.card_header_product)
        self.lbl_product_id_display.setObjectName(u"lbl_product_id_display")

        self.hboxLayout17.addWidget(self.lbl_product_id_display)


        self.layout_product_card.addWidget(self.card_header_product)

        self.frame_product_body = QFrame(self.frame_product_card)
        self.frame_product_body.setObjectName(u"frame_product_body")
        self.grid_product_form = QGridLayout(self.frame_product_body)
        self.grid_product_form.setObjectName(u"grid_product_form")
        self.grid_product_form.setHorizontalSpacing(16)
        self.grid_product_form.setVerticalSpacing(10)
        self.grid_product_form.setContentsMargins(20, 16, 20, 16)
        self.lbl_product_type = QLabel(self.frame_product_body)
        self.lbl_product_type.setObjectName(u"lbl_product_type")

        self.grid_product_form.addWidget(self.lbl_product_type, 0, 0, 1, 1)

        self.txt_product_type = QLineEdit(self.frame_product_body)
        self.txt_product_type.setObjectName(u"txt_product_type")
        self.txt_product_type.setMinimumSize(QSize(0, 36))
        self.txt_product_type.setMaximumSize(QSize(16777215, 36))

        self.grid_product_form.addWidget(self.txt_product_type, 1, 0, 1, 1)

        self.lbl_product_name = QLabel(self.frame_product_body)
        self.lbl_product_name.setObjectName(u"lbl_product_name")

        self.grid_product_form.addWidget(self.lbl_product_name, 2, 0, 1, 1)

        self.lbl_product_brand = QLabel(self.frame_product_body)
        self.lbl_product_brand.setObjectName(u"lbl_product_brand")

        self.grid_product_form.addWidget(self.lbl_product_brand, 2, 1, 1, 1)

        self.txt_product_name = QLineEdit(self.frame_product_body)
        self.txt_product_name.setObjectName(u"txt_product_name")
        self.txt_product_name.setMinimumSize(QSize(0, 36))
        self.txt_product_name.setMaximumSize(QSize(16777215, 36))

        self.grid_product_form.addWidget(self.txt_product_name, 3, 0, 1, 1)

        self.txt_product_brand = QLineEdit(self.frame_product_body)
        self.txt_product_brand.setObjectName(u"txt_product_brand")
        self.txt_product_brand.setMinimumSize(QSize(0, 36))
        self.txt_product_brand.setMaximumSize(QSize(16777215, 36))

        self.grid_product_form.addWidget(self.txt_product_brand, 3, 1, 1, 1)

        self.lbl_product_specification = QLabel(self.frame_product_body)
        self.lbl_product_specification.setObjectName(u"lbl_product_specification")

        self.grid_product_form.addWidget(self.lbl_product_specification, 4, 0, 1, 1)

        self.txt_product_specification = QLineEdit(self.frame_product_body)
        self.txt_product_specification.setObjectName(u"txt_product_specification")
        self.txt_product_specification.setMinimumSize(QSize(0, 36))
        self.txt_product_specification.setMaximumSize(QSize(16777215, 36))

        self.grid_product_form.addWidget(self.txt_product_specification, 5, 0, 1, 1)

        self.lbl_product_price = QLabel(self.frame_product_body)
        self.lbl_product_price.setObjectName(u"lbl_product_price")

        self.grid_product_form.addWidget(self.lbl_product_price, 6, 0, 1, 1)

        self.lbl_product_unit = QLabel(self.frame_product_body)
        self.lbl_product_unit.setObjectName(u"lbl_product_unit")

        self.grid_product_form.addWidget(self.lbl_product_unit, 6, 1, 1, 1)

        self.dspn_product_price = QDoubleSpinBox(self.frame_product_body)
        self.dspn_product_price.setObjectName(u"dspn_product_price")
        self.dspn_product_price.setMinimumSize(QSize(0, 36))
        self.dspn_product_price.setDecimals(2)
        self.dspn_product_price.setMaximum(999999.989999999990687)

        self.grid_product_form.addWidget(self.dspn_product_price, 7, 0, 1, 1)

        self.txt_product_unit = QLineEdit(self.frame_product_body)
        self.txt_product_unit.setObjectName(u"txt_product_unit")
        self.txt_product_unit.setMinimumSize(QSize(0, 36))
        self.txt_product_unit.setMaximumSize(QSize(16777215, 36))

        self.grid_product_form.addWidget(self.txt_product_unit, 7, 1, 1, 1)

        self.lbl_product_coverage_qty = QLabel(self.frame_product_body)
        self.lbl_product_coverage_qty.setObjectName(u"lbl_product_coverage_qty")

        self.grid_product_form.addWidget(self.lbl_product_coverage_qty, 8, 0, 1, 1)

        self.lbl_product_coverage_unit = QLabel(self.frame_product_body)
        self.lbl_product_coverage_unit.setObjectName(u"lbl_product_coverage_unit")

        self.grid_product_form.addWidget(self.lbl_product_coverage_unit, 8, 1, 1, 1)

        self.dspn_product_coverage_qty = QDoubleSpinBox(self.frame_product_body)
        self.dspn_product_coverage_qty.setObjectName(u"dspn_product_coverage_qty")
        self.dspn_product_coverage_qty.setMinimumSize(QSize(0, 36))
        self.dspn_product_coverage_qty.setDecimals(2)
        self.dspn_product_coverage_qty.setMaximum(999999.989999999990687)

        self.grid_product_form.addWidget(self.dspn_product_coverage_qty, 9, 0, 1, 1)

        self.txt_product_coverage_unit = QLineEdit(self.frame_product_body)
        self.txt_product_coverage_unit.setObjectName(u"txt_product_coverage_unit")
        self.txt_product_coverage_unit.setMinimumSize(QSize(0, 36))
        self.txt_product_coverage_unit.setMaximumSize(QSize(16777215, 36))

        self.grid_product_form.addWidget(self.txt_product_coverage_unit, 9, 1, 1, 1)

        self.lbl_product_unit_price_display = QLabel(self.frame_product_body)
        self.lbl_product_unit_price_display.setObjectName(u"lbl_product_unit_price_display")
        self.lbl_product_unit_price_display.setStyleSheet(u"font-size:13px; font-weight:700; color:#1565C0; background:transparent;")

        self.grid_product_form.addWidget(self.lbl_product_unit_price_display, 10, 0, 1, 2)

        self.txt_product_id = QLineEdit(self.frame_product_body)
        self.txt_product_id.setObjectName(u"txt_product_id")
        self.txt_product_id.setVisible(False)
        self.txt_product_id.setReadOnly(True)

        self.grid_product_form.addWidget(self.txt_product_id, 11, 0, 1, 1)


        self.layout_product_card.addWidget(self.frame_product_body)

        self.frame_product_footer = QFrame(self.frame_product_card)
        self.frame_product_footer.setObjectName(u"frame_product_footer")
        self.hboxLayout18 = QHBoxLayout(self.frame_product_footer)
        self.hboxLayout18.setObjectName(u"hboxLayout18")
        self.hboxLayout18.setContentsMargins(20, 12, 20, 12)
        self.spacerItem33 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout18.addItem(self.spacerItem33)

        self.btn_delete_product = QPushButton(self.frame_product_footer)
        self.btn_delete_product.setObjectName(u"btn_delete_product")
        self.btn_delete_product.setMinimumSize(QSize(90, 36))
        self.btn_delete_product.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout18.addWidget(self.btn_delete_product)

        self.btn_save_product = QPushButton(self.frame_product_footer)
        self.btn_save_product.setObjectName(u"btn_save_product")
        self.btn_save_product.setMinimumSize(QSize(110, 36))
        self.btn_save_product.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hboxLayout18.addWidget(self.btn_save_product)


        self.layout_product_card.addWidget(self.frame_product_footer)


        self.layout_tab_product_form.addWidget(self.frame_product_card)

        self.spacerItem34 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_tab_product_form.addItem(self.spacerItem34)

        self.tabWidget_products_page.addTab(self.tab_product_form, "")

        self.layout_products_page.addWidget(self.tabWidget_products_page)

        self.Pages.addWidget(self.pg_products)
        self.pg_settings = QWidget()
        self.pg_settings.setObjectName(u"pg_settings")
        self.layout_pg_settings_outer = QVBoxLayout(self.pg_settings)
        self.layout_pg_settings_outer.setObjectName(u"layout_pg_settings_outer")
        self.layout_pg_settings_outer.setContentsMargins(0, 0, 0, 0)
        self.scroll_settings_page = QScrollArea(self.pg_settings)
        self.scroll_settings_page.setObjectName(u"scroll_settings_page")
        self.scroll_settings_page.setFrameShape(QFrame.NoFrame)
        self.scroll_settings_page.setWidgetResizable(True)
        self.scroll_settings_page_contents = QWidget()
        self.scroll_settings_page_contents.setObjectName(u"scroll_settings_page_contents")
        self.scroll_settings_page_contents.setGeometry(QRect(0, 0, 1598, 992))
        self.layout_settings_contents = QVBoxLayout(self.scroll_settings_page_contents)
        self.layout_settings_contents.setObjectName(u"layout_settings_contents")
        self.layout_settings_contents.setContentsMargins(20, 20, 20, 20)
        self.grp_settings_company = QGroupBox(self.scroll_settings_page_contents)
        self.grp_settings_company.setObjectName(u"grp_settings_company")
        self.grid_settings_company = QGridLayout(self.grp_settings_company)
        self.grid_settings_company.setObjectName(u"grid_settings_company")
        self.grid_settings_company.setHorizontalSpacing(16)
        self.grid_settings_company.setVerticalSpacing(10)
        self.grid_settings_company.setContentsMargins(-1, 20, -1, -1)
        self.lbl_settings_company_name = QLabel(self.grp_settings_company)
        self.lbl_settings_company_name.setObjectName(u"lbl_settings_company_name")

        self.grid_settings_company.addWidget(self.lbl_settings_company_name, 0, 0, 1, 1)

        self.lbl_settings_company_tagline = QLabel(self.grp_settings_company)
        self.lbl_settings_company_tagline.setObjectName(u"lbl_settings_company_tagline")

        self.grid_settings_company.addWidget(self.lbl_settings_company_tagline, 0, 1, 1, 1)

        self.txt_settings_company_name = QLineEdit(self.grp_settings_company)
        self.txt_settings_company_name.setObjectName(u"txt_settings_company_name")
        self.txt_settings_company_name.setMinimumSize(QSize(0, 36))

        self.grid_settings_company.addWidget(self.txt_settings_company_name, 1, 0, 1, 1)

        self.txt_settings_company_tagline = QLineEdit(self.grp_settings_company)
        self.txt_settings_company_tagline.setObjectName(u"txt_settings_company_tagline")
        self.txt_settings_company_tagline.setMinimumSize(QSize(0, 36))

        self.grid_settings_company.addWidget(self.txt_settings_company_tagline, 1, 1, 1, 1)

        self.lbl_settings_company_phone = QLabel(self.grp_settings_company)
        self.lbl_settings_company_phone.setObjectName(u"lbl_settings_company_phone")

        self.grid_settings_company.addWidget(self.lbl_settings_company_phone, 2, 0, 1, 1)

        self.lbl_settings_company_email = QLabel(self.grp_settings_company)
        self.lbl_settings_company_email.setObjectName(u"lbl_settings_company_email")

        self.grid_settings_company.addWidget(self.lbl_settings_company_email, 2, 1, 1, 1)

        self.txt_settings_company_phone = QLineEdit(self.grp_settings_company)
        self.txt_settings_company_phone.setObjectName(u"txt_settings_company_phone")
        self.txt_settings_company_phone.setMinimumSize(QSize(0, 36))

        self.grid_settings_company.addWidget(self.txt_settings_company_phone, 3, 0, 1, 1)

        self.txt_settings_company_email = QLineEdit(self.grp_settings_company)
        self.txt_settings_company_email.setObjectName(u"txt_settings_company_email")
        self.txt_settings_company_email.setMinimumSize(QSize(0, 36))

        self.grid_settings_company.addWidget(self.txt_settings_company_email, 3, 1, 1, 1)

        self.lbl_settings_company_website = QLabel(self.grp_settings_company)
        self.lbl_settings_company_website.setObjectName(u"lbl_settings_company_website")

        self.grid_settings_company.addWidget(self.lbl_settings_company_website, 4, 0, 1, 2)

        self.txt_settings_company_website = QLineEdit(self.grp_settings_company)
        self.txt_settings_company_website.setObjectName(u"txt_settings_company_website")
        self.txt_settings_company_website.setMinimumSize(QSize(0, 36))

        self.grid_settings_company.addWidget(self.txt_settings_company_website, 5, 0, 1, 2)


        self.layout_settings_contents.addWidget(self.grp_settings_company)

        self.grp_settings_logo = QGroupBox(self.scroll_settings_page_contents)
        self.grp_settings_logo.setObjectName(u"grp_settings_logo")
        self.layout_settings_logo = QHBoxLayout(self.grp_settings_logo)
        self.layout_settings_logo.setObjectName(u"layout_settings_logo")
        self.layout_settings_logo.setContentsMargins(-1, 20, -1, -1)
        self.lbl_settings_logo_preview = QLabel(self.grp_settings_logo)
        self.lbl_settings_logo_preview.setObjectName(u"lbl_settings_logo_preview")
        self.lbl_settings_logo_preview.setMinimumSize(QSize(80, 80))
        self.lbl_settings_logo_preview.setMaximumSize(QSize(80, 80))
        self.lbl_settings_logo_preview.setStyleSheet(u"border: 1px solid #E3E8EE; border-radius: 6px; background-color: #F8FAFD;")
        self.lbl_settings_logo_preview.setScaledContents(True)
        self.lbl_settings_logo_preview.setAlignment(Qt.AlignCenter)

        self.layout_settings_logo.addWidget(self.lbl_settings_logo_preview)

        self.btn_settings_change_logo = QPushButton(self.grp_settings_logo)
        self.btn_settings_change_logo.setObjectName(u"btn_settings_change_logo")
        self.btn_settings_change_logo.setMinimumSize(QSize(0, 36))
        self.btn_settings_change_logo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.layout_settings_logo.addWidget(self.btn_settings_change_logo)

        self.spacerItem35 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_settings_logo.addItem(self.spacerItem35)


        self.layout_settings_contents.addWidget(self.grp_settings_logo)

        self.grp_settings_bank = QGroupBox(self.scroll_settings_page_contents)
        self.grp_settings_bank.setObjectName(u"grp_settings_bank")
        self.grid_settings_bank = QGridLayout(self.grp_settings_bank)
        self.grid_settings_bank.setObjectName(u"grid_settings_bank")
        self.grid_settings_bank.setHorizontalSpacing(16)
        self.grid_settings_bank.setVerticalSpacing(10)
        self.grid_settings_bank.setContentsMargins(-1, 20, -1, -1)
        self.lbl_settings_bank_account_no = QLabel(self.grp_settings_bank)
        self.lbl_settings_bank_account_no.setObjectName(u"lbl_settings_bank_account_no")

        self.grid_settings_bank.addWidget(self.lbl_settings_bank_account_no, 0, 0, 1, 1)

        self.lbl_settings_bank_account_name = QLabel(self.grp_settings_bank)
        self.lbl_settings_bank_account_name.setObjectName(u"lbl_settings_bank_account_name")

        self.grid_settings_bank.addWidget(self.lbl_settings_bank_account_name, 0, 1, 1, 1)

        self.txt_settings_bank_account_no = QLineEdit(self.grp_settings_bank)
        self.txt_settings_bank_account_no.setObjectName(u"txt_settings_bank_account_no")
        self.txt_settings_bank_account_no.setMinimumSize(QSize(0, 36))

        self.grid_settings_bank.addWidget(self.txt_settings_bank_account_no, 1, 0, 1, 1)

        self.txt_settings_bank_account_name = QLineEdit(self.grp_settings_bank)
        self.txt_settings_bank_account_name.setObjectName(u"txt_settings_bank_account_name")
        self.txt_settings_bank_account_name.setMinimumSize(QSize(0, 36))

        self.grid_settings_bank.addWidget(self.txt_settings_bank_account_name, 1, 1, 1, 1)

        self.lbl_settings_bank_details = QLabel(self.grp_settings_bank)
        self.lbl_settings_bank_details.setObjectName(u"lbl_settings_bank_details")

        self.grid_settings_bank.addWidget(self.lbl_settings_bank_details, 2, 0, 1, 2)

        self.txt_settings_bank_details = QLineEdit(self.grp_settings_bank)
        self.txt_settings_bank_details.setObjectName(u"txt_settings_bank_details")
        self.txt_settings_bank_details.setMinimumSize(QSize(0, 36))

        self.grid_settings_bank.addWidget(self.txt_settings_bank_details, 3, 0, 1, 2)


        self.layout_settings_contents.addWidget(self.grp_settings_bank)

        self.grp_settings_payment_methods = QGroupBox(self.scroll_settings_page_contents)
        self.grp_settings_payment_methods.setObjectName(u"grp_settings_payment_methods")
        self.layout_settings_payment_methods = QHBoxLayout(self.grp_settings_payment_methods)
        self.layout_settings_payment_methods.setObjectName(u"layout_settings_payment_methods")
        self.layout_settings_payment_methods.setContentsMargins(-1, 20, -1, -1)
        self.chk_settings_pm_zelle = QCheckBox(self.grp_settings_payment_methods)
        self.chk_settings_pm_zelle.setObjectName(u"chk_settings_pm_zelle")

        self.layout_settings_payment_methods.addWidget(self.chk_settings_pm_zelle)

        self.chk_settings_pm_check = QCheckBox(self.grp_settings_payment_methods)
        self.chk_settings_pm_check.setObjectName(u"chk_settings_pm_check")

        self.layout_settings_payment_methods.addWidget(self.chk_settings_pm_check)

        self.chk_settings_pm_cash = QCheckBox(self.grp_settings_payment_methods)
        self.chk_settings_pm_cash.setObjectName(u"chk_settings_pm_cash")

        self.layout_settings_payment_methods.addWidget(self.chk_settings_pm_cash)

        self.chk_settings_pm_bank_transfer = QCheckBox(self.grp_settings_payment_methods)
        self.chk_settings_pm_bank_transfer.setObjectName(u"chk_settings_pm_bank_transfer")

        self.layout_settings_payment_methods.addWidget(self.chk_settings_pm_bank_transfer)

        self.chk_settings_pm_credit_card = QCheckBox(self.grp_settings_payment_methods)
        self.chk_settings_pm_credit_card.setObjectName(u"chk_settings_pm_credit_card")

        self.layout_settings_payment_methods.addWidget(self.chk_settings_pm_credit_card)

        self.spacerItem36 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_settings_payment_methods.addItem(self.spacerItem36)


        self.layout_settings_contents.addWidget(self.grp_settings_payment_methods)

        self.grp_settings_email = QGroupBox(self.scroll_settings_page_contents)
        self.grp_settings_email.setObjectName(u"grp_settings_email")
        self.grid_settings_email = QGridLayout(self.grp_settings_email)
        self.grid_settings_email.setObjectName(u"grid_settings_email")
        self.grid_settings_email.setHorizontalSpacing(16)
        self.grid_settings_email.setVerticalSpacing(10)
        self.grid_settings_email.setContentsMargins(-1, 20, -1, -1)
        self.lbl_settings_smtp_host = QLabel(self.grp_settings_email)
        self.lbl_settings_smtp_host.setObjectName(u"lbl_settings_smtp_host")

        self.grid_settings_email.addWidget(self.lbl_settings_smtp_host, 0, 0, 1, 1)

        self.lbl_settings_smtp_port = QLabel(self.grp_settings_email)
        self.lbl_settings_smtp_port.setObjectName(u"lbl_settings_smtp_port")

        self.grid_settings_email.addWidget(self.lbl_settings_smtp_port, 0, 1, 1, 1)

        self.txt_settings_smtp_host = QLineEdit(self.grp_settings_email)
        self.txt_settings_smtp_host.setObjectName(u"txt_settings_smtp_host")
        self.txt_settings_smtp_host.setMinimumSize(QSize(0, 36))

        self.grid_settings_email.addWidget(self.txt_settings_smtp_host, 1, 0, 1, 1)

        self.spn_settings_smtp_port = QSpinBox(self.grp_settings_email)
        self.spn_settings_smtp_port.setObjectName(u"spn_settings_smtp_port")
        self.spn_settings_smtp_port.setMinimumSize(QSize(0, 36))
        self.spn_settings_smtp_port.setMinimum(1)
        self.spn_settings_smtp_port.setMaximum(65535)
        self.spn_settings_smtp_port.setValue(587)

        self.grid_settings_email.addWidget(self.spn_settings_smtp_port, 1, 1, 1, 1)

        self.lbl_settings_smtp_user = QLabel(self.grp_settings_email)
        self.lbl_settings_smtp_user.setObjectName(u"lbl_settings_smtp_user")

        self.grid_settings_email.addWidget(self.lbl_settings_smtp_user, 2, 0, 1, 1)

        self.lbl_settings_smtp_password = QLabel(self.grp_settings_email)
        self.lbl_settings_smtp_password.setObjectName(u"lbl_settings_smtp_password")

        self.grid_settings_email.addWidget(self.lbl_settings_smtp_password, 2, 1, 1, 1)

        self.txt_settings_smtp_user = QLineEdit(self.grp_settings_email)
        self.txt_settings_smtp_user.setObjectName(u"txt_settings_smtp_user")
        self.txt_settings_smtp_user.setMinimumSize(QSize(0, 36))

        self.grid_settings_email.addWidget(self.txt_settings_smtp_user, 3, 0, 1, 1)

        self.txt_settings_smtp_password = QLineEdit(self.grp_settings_email)
        self.txt_settings_smtp_password.setObjectName(u"txt_settings_smtp_password")
        self.txt_settings_smtp_password.setMinimumSize(QSize(0, 36))
        self.txt_settings_smtp_password.setEchoMode(QLineEdit.Password)

        self.grid_settings_email.addWidget(self.txt_settings_smtp_password, 3, 1, 1, 1)

        self.lbl_settings_smtp_hint = QLabel(self.grp_settings_email)
        self.lbl_settings_smtp_hint.setObjectName(u"lbl_settings_smtp_hint")
        self.lbl_settings_smtp_hint.setStyleSheet(u"font-size:11px; color:#6B7C93; background:transparent;")
        self.lbl_settings_smtp_hint.setWordWrap(True)

        self.grid_settings_email.addWidget(self.lbl_settings_smtp_hint, 4, 0, 1, 2)


        self.layout_settings_contents.addWidget(self.grp_settings_email)

        self.btn_settings_save = QPushButton(self.scroll_settings_page_contents)
        self.btn_settings_save.setObjectName(u"btn_settings_save")
        self.btn_settings_save.setMinimumSize(QSize(0, 44))
        self.btn_settings_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_settings_save.setStyleSheet(u"QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 8px; font-size: 14px; font-weight: 700; } QPushButton:hover { background-color: #1E88E5; }")

        self.layout_settings_contents.addWidget(self.btn_settings_save)

        self.scroll_settings_page.setWidget(self.scroll_settings_page_contents)

        self.layout_pg_settings_outer.addWidget(self.scroll_settings_page)

        self.Pages.addWidget(self.pg_settings)

        self.verticalLayout_main.addWidget(self.Pages)


        self.horizontalLayout_root.addWidget(self.Main_container)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.Pages.setCurrentIndex(1)
        self.tabWidget_jobs.setCurrentIndex(0)
        self.tabWidget_products_page.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"VL Flooring", None))
#if QT_CONFIG(tooltip)
        self.btn_toggle.setToolTip(QCoreApplication.translate("MainWindow", u"Toggle menu", None))
#endif // QT_CONFIG(tooltip)
        self.btn_toggle.setText("")
        self.label_logo.setText(QCoreApplication.translate("MainWindow", u"<html><body><p align=\"center\"><span style=\"font-size:13pt;\">VL FLOORING</span></p></body></html>", None))
#if QT_CONFIG(tooltip)
        self.btn_home.setToolTip(QCoreApplication.translate("MainWindow", u"Home", None))
#endif // QT_CONFIG(tooltip)
        self.btn_home.setText("")
#if QT_CONFIG(tooltip)
        self.btn_jobs.setToolTip(QCoreApplication.translate("MainWindow", u"Job Records", None))
#endif // QT_CONFIG(tooltip)
        self.btn_jobs.setText("")
#if QT_CONFIG(tooltip)
        self.btn_registrations.setToolTip(QCoreApplication.translate("MainWindow", u"Registrations", None))
#endif // QT_CONFIG(tooltip)
        self.btn_registrations.setText("")
#if QT_CONFIG(tooltip)
        self.btn_reg_companies.setToolTip(QCoreApplication.translate("MainWindow", u"Companies", None))
#endif // QT_CONFIG(tooltip)
        self.btn_reg_companies.setText("")
#if QT_CONFIG(tooltip)
        self.btn_reg_contractors.setToolTip(QCoreApplication.translate("MainWindow", u"Contractors", None))
#endif // QT_CONFIG(tooltip)
        self.btn_reg_contractors.setText("")
#if QT_CONFIG(tooltip)
        self.btn_reg_work_types.setToolTip(QCoreApplication.translate("MainWindow", u"Work Types", None))
#endif // QT_CONFIG(tooltip)
        self.btn_reg_work_types.setText("")
#if QT_CONFIG(tooltip)
        self.btn_reg_products.setToolTip(QCoreApplication.translate("MainWindow", u"Products", None))
#endif // QT_CONFIG(tooltip)
        self.btn_reg_products.setText("")
#if QT_CONFIG(tooltip)
        self.btn_nav_receivables.setToolTip(QCoreApplication.translate("MainWindow", u"Receivables", None))
#endif // QT_CONFIG(tooltip)
        self.btn_nav_receivables.setText("")
#if QT_CONFIG(tooltip)
        self.btn_customer.setToolTip(QCoreApplication.translate("MainWindow", u"Customer", None))
#endif // QT_CONFIG(tooltip)
        self.btn_customer.setText("")
#if QT_CONFIG(tooltip)
        self.btn_user.setToolTip(QCoreApplication.translate("MainWindow", u"User", None))
#endif // QT_CONFIG(tooltip)
        self.btn_user.setText("")
#if QT_CONFIG(tooltip)
        self.btn_settings.setToolTip(QCoreApplication.translate("MainWindow", u"Settings", None))
#endif // QT_CONFIG(tooltip)
        self.btn_settings.setText("")
        self.Top_label.setText(QCoreApplication.translate("MainWindow", u"Dashboard", None))
        self.lbl_user.setText(QCoreApplication.translate("MainWindow", u"\u25cf Admin", None))
        self.lbl_home_jobs_month_icon.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:20px; background:transparent;", None))
        self.lbl_home_jobs_month_icon.setText(QCoreApplication.translate("MainWindow", u"\U0001f6e0\U0000fe0f", None))
        self.lbl_home_jobs_month_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:24px; font-weight:800; color:#1A1F36; background:transparent;", None))
        self.lbl_home_jobs_month_value.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.lbl_home_jobs_month_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_home_jobs_month_label.setText(QCoreApplication.translate("MainWindow", u"Jobs This Month", None))
        self.lbl_home_revenue_month_icon.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:20px; background:transparent;", None))
        self.lbl_home_revenue_month_icon.setText(QCoreApplication.translate("MainWindow", u"\U0001f4b0", None))
        self.lbl_home_revenue_month_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:24px; font-weight:800; color:#1A1F36; background:transparent;", None))
        self.lbl_home_revenue_month_value.setText(QCoreApplication.translate("MainWindow", u"$0.00", None))
        self.lbl_home_revenue_month_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_home_revenue_month_label.setText(QCoreApplication.translate("MainWindow", u"Revenue This Month", None))
        self.lbl_home_overdue_icon.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:20px; background:transparent;", None))
        self.lbl_home_overdue_icon.setText(QCoreApplication.translate("MainWindow", u"\u26a0\ufe0f", None))
        self.lbl_home_overdue_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:24px; font-weight:800; color:#C62828; background:transparent;", None))
        self.lbl_home_overdue_value.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.lbl_home_overdue_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_home_overdue_label.setText(QCoreApplication.translate("MainWindow", u"Overdue Invoices", None))
        self.lbl_home_pending_jobs_icon.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:20px; background:transparent;", None))
        self.lbl_home_pending_jobs_icon.setText(QCoreApplication.translate("MainWindow", u"\u23f3", None))
        self.lbl_home_pending_jobs_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:24px; font-weight:800; color:#1A1F36; background:transparent;", None))
        self.lbl_home_pending_jobs_value.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.lbl_home_pending_jobs_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_home_pending_jobs_label.setText(QCoreApplication.translate("MainWindow", u"Pending Jobs", None))
        self.btn_home_new_job.setText(QCoreApplication.translate("MainWindow", u"+  New Job", None))
        self.btn_home_generate_invoices.setText(QCoreApplication.translate("MainWindow", u"\U0001f9fe  Generate Invoices", None))
        self.btn_home_schedule.setText(QCoreApplication.translate("MainWindow", u"\U0001f4c5  Schedule", None))
        self.btn_home_new_customer.setText(QCoreApplication.translate("MainWindow", u"\U0001f464  New Customer", None))
        self.lbl_home_recent_jobs_title.setText(QCoreApplication.translate("MainWindow", u"Recent Jobs", None))
        ___qtablewidgetitem = self.table_home_recent_jobs.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"Date", None))
        ___qtablewidgetitem1 = self.table_home_recent_jobs.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"Contractor", None))
        ___qtablewidgetitem2 = self.table_home_recent_jobs.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Client", None))
        ___qtablewidgetitem3 = self.table_home_recent_jobs.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"Value", None))
        ___qtablewidgetitem4 = self.table_home_recent_jobs.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"Status", None))
        self.lbl_home_chart_title.setText(QCoreApplication.translate("MainWindow", u"Revenue \u2014 Last 6 Months", None))
        self.lbl_home_work_types_title.setText(QCoreApplication.translate("MainWindow", u"Most Performed Work Types", None))
        self.lbl_home_work_type_1_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:20px; font-weight:800; color:#1A1F36; background:transparent;", None))
        self.lbl_home_work_type_1_value.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_home_work_type_1_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_home_work_type_1_label.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_home_work_type_2_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:20px; font-weight:800; color:#1A1F36; background:transparent;", None))
        self.lbl_home_work_type_2_value.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_home_work_type_2_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_home_work_type_2_label.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_home_work_type_3_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:20px; font-weight:800; color:#1A1F36; background:transparent;", None))
        self.lbl_home_work_type_3_value.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_home_work_type_3_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_home_work_type_3_label.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_home_work_type_4_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:20px; font-weight:800; color:#1A1F36; background:transparent;", None))
        self.lbl_home_work_type_4_value.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_home_work_type_4_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_home_work_type_4_label.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.txt_search_jobs.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\U0001f50d  Search by address, contractor, city, job code\U00002026", None))
        self.cmb_filter_status.setItemText(0, QCoreApplication.translate("MainWindow", u"All Status", None))
        self.cmb_filter_status.setItemText(1, QCoreApplication.translate("MainWindow", u"PENDING", None))
        self.cmb_filter_status.setItemText(2, QCoreApplication.translate("MainWindow", u"STARTED", None))
        self.cmb_filter_status.setItemText(3, QCoreApplication.translate("MainWindow", u"IN_PROGRESS", None))
        self.cmb_filter_status.setItemText(4, QCoreApplication.translate("MainWindow", u"COMPLETED", None))
        self.cmb_filter_status.setItemText(5, QCoreApplication.translate("MainWindow", u"CANCELLED", None))

#if QT_CONFIG(tooltip)
        self.date_filter_from.setToolTip(QCoreApplication.translate("MainWindow", u"Date from", None))
#endif // QT_CONFIG(tooltip)
        self.date_filter_from.setDisplayFormat(QCoreApplication.translate("MainWindow", u"MM/dd/yyyy", None))
#if QT_CONFIG(tooltip)
        self.date_filter_to.setToolTip(QCoreApplication.translate("MainWindow", u"Date to", None))
#endif // QT_CONFIG(tooltip)
        self.date_filter_to.setDisplayFormat(QCoreApplication.translate("MainWindow", u"MM/dd/yyyy", None))
        self.btn_refresh_jobs.setText(QCoreApplication.translate("MainWindow", u"\u21bb  Refresh", None))
        self.btn_export_excel_jobs.setText(QCoreApplication.translate("MainWindow", u"\u2913  Excel", None))
        self.btn_export_pdf_jobs.setText(QCoreApplication.translate("MainWindow", u"\u2913  PDF", None))
#if QT_CONFIG(tooltip)
        self.btn_split_daily_total.setToolTip(QCoreApplication.translate("MainWindow", u"Split a day's total payment across the jobs done that day", None))
#endif // QT_CONFIG(tooltip)
        self.btn_split_daily_total.setText(QCoreApplication.translate("MainWindow", u"\U0001f500  Split Daily Total", None))
#if QT_CONFIG(tooltip)
        self.btn_view_project.setToolTip(QCoreApplication.translate("MainWindow", u"Show all jobs under the selected row's Job Code", None))
#endif // QT_CONFIG(tooltip)
        self.btn_view_project.setText(QCoreApplication.translate("MainWindow", u"\U0001f5c2  View Project", None))
#if QT_CONFIG(tooltip)
        self.btn_clean_empty_job_codes.setToolTip(QCoreApplication.translate("MainWindow", u"Find and remove Job Codes that have no jobs linked to them", None))
#endif // QT_CONFIG(tooltip)
        self.btn_clean_empty_job_codes.setText(QCoreApplication.translate("MainWindow", u"\U0001f9f9  Clean Empty Job Codes", None))
        self.btn_toggle_table_expanded.setText(QCoreApplication.translate("MainWindow", u"\u26f6  Expand Table", None))
        ___qtablewidgetitem5 = self.table_work_days.horizontalHeaderItem(0)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("MainWindow", u"ID", None))
        ___qtablewidgetitem6 = self.table_work_days.horizontalHeaderItem(1)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("MainWindow", u"Work Date", None))
        ___qtablewidgetitem7 = self.table_work_days.horizontalHeaderItem(2)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("MainWindow", u"Contractor", None))
        ___qtablewidgetitem8 = self.table_work_days.horizontalHeaderItem(3)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("MainWindow", u"Company", None))
        ___qtablewidgetitem9 = self.table_work_days.horizontalHeaderItem(4)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("MainWindow", u"Client", None))
        ___qtablewidgetitem10 = self.table_work_days.horizontalHeaderItem(5)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("MainWindow", u"Job Address", None))
        ___qtablewidgetitem11 = self.table_work_days.horizontalHeaderItem(6)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("MainWindow", u"City", None))
        ___qtablewidgetitem12 = self.table_work_days.horizontalHeaderItem(7)
        ___qtablewidgetitem12.setText(QCoreApplication.translate("MainWindow", u"State", None))
        ___qtablewidgetitem13 = self.table_work_days.horizontalHeaderItem(8)
        ___qtablewidgetitem13.setText(QCoreApplication.translate("MainWindow", u"Demolition", None))
        ___qtablewidgetitem14 = self.table_work_days.horizontalHeaderItem(9)
        ___qtablewidgetitem14.setText(QCoreApplication.translate("MainWindow", u"Installation", None))
        ___qtablewidgetitem15 = self.table_work_days.horizontalHeaderItem(10)
        ___qtablewidgetitem15.setText(QCoreApplication.translate("MainWindow", u"Preparation", None))
        ___qtablewidgetitem16 = self.table_work_days.horizontalHeaderItem(11)
        ___qtablewidgetitem16.setText(QCoreApplication.translate("MainWindow", u"Others", None))
        ___qtablewidgetitem17 = self.table_work_days.horizontalHeaderItem(12)
        ___qtablewidgetitem17.setText(QCoreApplication.translate("MainWindow", u"Repair", None))
        ___qtablewidgetitem18 = self.table_work_days.horizontalHeaderItem(13)
        ___qtablewidgetitem18.setText(QCoreApplication.translate("MainWindow", u"Value", None))
        ___qtablewidgetitem19 = self.table_work_days.horizontalHeaderItem(14)
        ___qtablewidgetitem19.setText(QCoreApplication.translate("MainWindow", u"Status", None))
        ___qtablewidgetitem20 = self.table_work_days.horizontalHeaderItem(15)
        ___qtablewidgetitem20.setText(QCoreApplication.translate("MainWindow", u"Job Code", None))
        self.btn_new_job.setText(QCoreApplication.translate("MainWindow", u"+  New Job", None))
#if QT_CONFIG(tooltip)
        self.btn_job_go_to_expense.setToolTip(QCoreApplication.translate("MainWindow", u"Go to New/Edit Expense", None))
#endif // QT_CONFIG(tooltip)
        self.btn_job_go_to_expense.setText(QCoreApplication.translate("MainWindow", u"Expense", None))
        self.lbl_form_title.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:15px; font-weight:700; color:#FFFFFF; background:transparent;", None))
        self.lbl_form_title.setText(QCoreApplication.translate("MainWindow", u"Work Day Record", None))
        self.lbl_job_id_display.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; color:#90B8E0; background:transparent;", None))
        self.lbl_job_id_display.setText(QCoreApplication.translate("MainWindow", u"#ID: \u2014", None))
        self.btn_toggle_client_drawer.setText(QCoreApplication.translate("MainWindow", u"\U0001f464  Client Info", None))
        self.spacer_lbl.setText("")
        self.lbl_job_info_title.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:15px; font-weight:700; color:#6B7C93; background:transparent;", None))
        self.lbl_job_info_title.setText(QCoreApplication.translate("MainWindow", u"Job Info", None))
        self.lbl_work_date.setText(QCoreApplication.translate("MainWindow", u"WORK DATE", None))
        self.lbl_job_code.setText(QCoreApplication.translate("MainWindow", u"JOB CODE", None))
        self.lbl_payment.setText(QCoreApplication.translate("MainWindow", u"PAYMENT METHOD", None))
        self.date_work_date.setDisplayFormat(QCoreApplication.translate("MainWindow", u"MM/dd/yyyy", None))
#if QT_CONFIG(tooltip)
        self.cmb_job_code.setToolTip(QCoreApplication.translate("MainWindow", u"Type or pick an existing job code \u2014 links multiple work days under the same project", None))
#endif // QT_CONFIG(tooltip)
        self.btn_generate_job_code.setText(QCoreApplication.translate("MainWindow", u"+ Generate Code", None))
        self.lbl_days_worked_value.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.cmb_payment.setItemText(0, QCoreApplication.translate("MainWindow", u"Receivable", None))
        self.cmb_payment.setItemText(1, QCoreApplication.translate("MainWindow", u"Paid", None))

        self.lbl_contractor.setText(QCoreApplication.translate("MainWindow", u"CONTRACTOR", None))
        self.lbl_company_form.setText(QCoreApplication.translate("MainWindow", u"COMPANY", None))
        self.lbl_status_form.setText(QCoreApplication.translate("MainWindow", u"STATUS", None))
        self.lbl_value.setText(QCoreApplication.translate("MainWindow", u"VALUE ($)", None))
        self.cmb_status_form.setItemText(0, QCoreApplication.translate("MainWindow", u"PENDING", None))
        self.cmb_status_form.setItemText(1, QCoreApplication.translate("MainWindow", u"STARTED", None))
        self.cmb_status_form.setItemText(2, QCoreApplication.translate("MainWindow", u"IN_PROGRESS", None))
        self.cmb_status_form.setItemText(3, QCoreApplication.translate("MainWindow", u"COMPLETED", None))
        self.cmb_status_form.setItemText(4, QCoreApplication.translate("MainWindow", u"CANCELLED", None))

        self.dspn_value.setPrefix(QCoreApplication.translate("MainWindow", u"$ ", None))
        self.lbl_work_types_title.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:15px; font-weight:700; color:#6B7C93; background:transparent;", None))
        self.lbl_work_types_title.setText(QCoreApplication.translate("MainWindow", u"Work Types", None))
        self.chk_demolition.setText("")
        self.lbl_demolition.setText(QCoreApplication.translate("MainWindow", u"DEMOLITION / REMOVE", None))
        self.lbl_unit_demolition.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_demolition.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_unit_demolition_2.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_demolition_2.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_unit_demolition_3.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_demolition_3.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_unit_demolition_4.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_demolition_4.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.chk_preparation.setText("")
        self.lbl_preparation.setText(QCoreApplication.translate("MainWindow", u"PREPARATION", None))
        self.lbl_unit_preparation.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_preparation.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_unit_preparation_2.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_preparation_2.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_unit_preparation_3.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_preparation_3.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_unit_preparation_4.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_preparation_4.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.chk_installation.setText("")
        self.lbl_installation.setText(QCoreApplication.translate("MainWindow", u"INSTALLATION", None))
        self.lbl_unit_installation.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_installation.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_unit_installation_2.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_installation_2.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_unit_installation_3.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_installation_3.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_unit_installation_4.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_installation_4.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.chk_others.setText("")
        self.lbl_others.setText(QCoreApplication.translate("MainWindow", u"OTHERS", None))
        self.lbl_unit_others.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_others.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_unit_others_2.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_others_2.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.chk_reparo.setText("")
        self.lbl_reparo.setText(QCoreApplication.translate("MainWindow", u"REPARO", None))
        self.lbl_unit_reparo.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_reparo.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_unit_reparo_2.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93;", None))
        self.lbl_unit_reparo_2.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.lbl_note.setText(QCoreApplication.translate("MainWindow", u"NOTE", None))
        self.txt_note.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Additional notes\u2026", None))
        self.frame_job_footer.setStyleSheet(QCoreApplication.translate("MainWindow", u"QFrame { background-color:#F8FAFD; border-top: 1px solid #EEF2F7; border-radius:0px; border-bottom-left-radius:8px; border-bottom-right-radius:8px; }", None))
        self.btn_delete_job.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.btn_save_job.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.lbl_client_info_title.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:15px; font-weight:700; color:#6B7C93; background:transparent;", None))
        self.lbl_client_info_title.setText(QCoreApplication.translate("MainWindow", u"Client Info", None))
        self.lbl_job_address.setText(QCoreApplication.translate("MainWindow", u"CLIENT ADDRESS", None))
        self.lbl_job_address2.setText(QCoreApplication.translate("MainWindow", u"ADDRESS LINE 2 (APT / SUITE)", None))
#if QT_CONFIG(tooltip)
        self.cmb_client_address.setToolTip(QCoreApplication.translate("MainWindow", u"Select a previously used address or type a new one to create it automatically", None))
#endif // QT_CONFIG(tooltip)
        self.txt_client_address2.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Apt, Suite, Unit\u2026", None))
        self.lbl_state.setText(QCoreApplication.translate("MainWindow", u"STATE", None))
        self.lbl_city.setText(QCoreApplication.translate("MainWindow", u"CITY", None))
        self.lbl_zip.setText(QCoreApplication.translate("MainWindow", u"ZIP CODE", None))
        self.txt_client_zip.setPlaceholderText(QCoreApplication.translate("MainWindow", u"00000-000", None))
        self.lbl_client.setText(QCoreApplication.translate("MainWindow", u"CLIENT NAME", None))
        self.lbl_phone.setText(QCoreApplication.translate("MainWindow", u"CLIENT PHONE", None))
#if QT_CONFIG(tooltip)
        self.txt_client_name.setToolTip(QCoreApplication.translate("MainWindow", u"Type the client's name \u2014 matches an existing client or creates a new one automatically", None))
#endif // QT_CONFIG(tooltip)
        self.txt_client_name.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Client name\u2026", None))
        self.txt_client_phone.setPlaceholderText(QCoreApplication.translate("MainWindow", u"(000) 000 - 0000", None))
        self.lbl_client_email.setText(QCoreApplication.translate("MainWindow", u"CLIENT EMAIL", None))
        self.lbl_phone_2.setText(QCoreApplication.translate("MainWindow", u"CLIENT PHONE 2", None))
        self.txt_client_email.setPlaceholderText(QCoreApplication.translate("MainWindow", u"email@example.com", None))
        self.txt_client_phone_2.setPlaceholderText(QCoreApplication.translate("MainWindow", u"(000) 000 - 0000", None))
        self.lbl_materials_title.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:15px; font-weight:700; color:#FFFFFF; background:transparent;", None))
        self.lbl_materials_title.setText(QCoreApplication.translate("MainWindow", u"Materials Used", None))
        ___qtablewidgetitem21 = self.table_job_materials.horizontalHeaderItem(0)
        ___qtablewidgetitem21.setText(QCoreApplication.translate("MainWindow", u"Product", None))
        ___qtablewidgetitem22 = self.table_job_materials.horizontalHeaderItem(1)
        ___qtablewidgetitem22.setText(QCoreApplication.translate("MainWindow", u"Qty", None))
        ___qtablewidgetitem23 = self.table_job_materials.horizontalHeaderItem(2)
        ___qtablewidgetitem23.setText(QCoreApplication.translate("MainWindow", u"Unit", None))
        self.btn_add_material.setText(QCoreApplication.translate("MainWindow", u"+ Add", None))
        self.btn_remove_material.setText(QCoreApplication.translate("MainWindow", u"Remove Selected", None))
        self.lbl_materials_total_cost.setText("")
        self.tabWidget_jobs.setTabText(self.tabWidget_jobs.indexOf(self.tab_jobs_master), QCoreApplication.translate("MainWindow", u"Work Days", None))
        self.lbl_schedule_selected_date.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:16px; font-weight:700; color:#1C2B3A; background:transparent;", None))
        self.lbl_schedule_selected_date.setText(QCoreApplication.translate("MainWindow", u"Jobs on this day", None))
        self.btn_schedule_new_job.setText(QCoreApplication.translate("MainWindow", u"+  New Job on This Day", None))
        self.tabWidget_jobs.setTabText(self.tabWidget_jobs.indexOf(self.tab_schedule), QCoreApplication.translate("MainWindow", u"Schedule", None))
        self.txt_search_companies.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\U0001f50d  Search by name, contact, city\U00002026", None))
        self.cmb_filter_company_status.setItemText(0, QCoreApplication.translate("MainWindow", u"All Status", None))
        self.cmb_filter_company_status.setItemText(1, QCoreApplication.translate("MainWindow", u"ACTIVE", None))
        self.cmb_filter_company_status.setItemText(2, QCoreApplication.translate("MainWindow", u"INACTIVE", None))

        self.btn_refresh_companies.setText(QCoreApplication.translate("MainWindow", u"\u21bb  Refresh", None))
        self.btn_export_excel_companies.setText(QCoreApplication.translate("MainWindow", u"\u2913  Excel", None))
        self.btn_export_pdf_companies.setText(QCoreApplication.translate("MainWindow", u"\u2913  PDF", None))
        self.btn_new_company.setText(QCoreApplication.translate("MainWindow", u"+  New Company", None))
        self.btn_toggle_companies_table_expanded.setText(QCoreApplication.translate("MainWindow", u"\u26f6  Expand Table", None))
        ___qtablewidgetitem24 = self.table_companies.horizontalHeaderItem(0)
        ___qtablewidgetitem24.setText(QCoreApplication.translate("MainWindow", u"ID", None))
        ___qtablewidgetitem25 = self.table_companies.horizontalHeaderItem(1)
        ___qtablewidgetitem25.setText(QCoreApplication.translate("MainWindow", u"Company Name", None))
        ___qtablewidgetitem26 = self.table_companies.horizontalHeaderItem(2)
        ___qtablewidgetitem26.setText(QCoreApplication.translate("MainWindow", u"Contact Name", None))
        ___qtablewidgetitem27 = self.table_companies.horizontalHeaderItem(3)
        ___qtablewidgetitem27.setText(QCoreApplication.translate("MainWindow", u"Email", None))
        ___qtablewidgetitem28 = self.table_companies.horizontalHeaderItem(4)
        ___qtablewidgetitem28.setText(QCoreApplication.translate("MainWindow", u"Phone", None))
        ___qtablewidgetitem29 = self.table_companies.horizontalHeaderItem(5)
        ___qtablewidgetitem29.setText(QCoreApplication.translate("MainWindow", u"Phone 2", None))
        ___qtablewidgetitem30 = self.table_companies.horizontalHeaderItem(6)
        ___qtablewidgetitem30.setText(QCoreApplication.translate("MainWindow", u"Address", None))
        ___qtablewidgetitem31 = self.table_companies.horizontalHeaderItem(7)
        ___qtablewidgetitem31.setText(QCoreApplication.translate("MainWindow", u"City", None))
        ___qtablewidgetitem32 = self.table_companies.horizontalHeaderItem(8)
        ___qtablewidgetitem32.setText(QCoreApplication.translate("MainWindow", u"State", None))
        ___qtablewidgetitem33 = self.table_companies.horizontalHeaderItem(9)
        ___qtablewidgetitem33.setText(QCoreApplication.translate("MainWindow", u"Zip Code", None))
        ___qtablewidgetitem34 = self.table_companies.horizontalHeaderItem(10)
        ___qtablewidgetitem34.setText(QCoreApplication.translate("MainWindow", u"Website", None))
        ___qtablewidgetitem35 = self.table_companies.horizontalHeaderItem(11)
        ___qtablewidgetitem35.setText(QCoreApplication.translate("MainWindow", u"Status", None))
        self.lbl_company_form_title.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:15px; font-weight:700; color:#FFFFFF; background:transparent;", None))
        self.lbl_company_form_title.setText(QCoreApplication.translate("MainWindow", u"Company Record", None))
        self.lbl_company_id_display.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; color:#90B8E0; background:transparent;", None))
        self.lbl_company_id_display.setText(QCoreApplication.translate("MainWindow", u"#ID: \u2014", None))
        self.lbl_company_name.setText(QCoreApplication.translate("MainWindow", u"COMPANY NAME", None))
        self.lbl_contact_name.setText(QCoreApplication.translate("MainWindow", u"CONTACT NAME", None))
        self.txt_company_name.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Company name\u2026", None))
        self.txt_contact_name.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Contact person\u2026", None))
        self.lbl_company_email.setText(QCoreApplication.translate("MainWindow", u"EMAIL", None))
        self.lbl_company_phone.setText(QCoreApplication.translate("MainWindow", u"PHONE NUMBER", None))
        self.lbl_company_phone2.setText(QCoreApplication.translate("MainWindow", u"PHONE NUMBER 2", None))
        self.txt_company_email.setPlaceholderText(QCoreApplication.translate("MainWindow", u"email@company.com", None))
        self.txt_company_phone.setPlaceholderText(QCoreApplication.translate("MainWindow", u"(000) 000-0000", None))
        self.txt_company_phone2.setPlaceholderText(QCoreApplication.translate("MainWindow", u"(000) 000-0000", None))
        self.div_company_1.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color:#EEF2F7; border-radius:0px;", None))
        self.lbl_company_address.setText(QCoreApplication.translate("MainWindow", u"ADDRESS", None))
        self.lbl_company_address2.setText(QCoreApplication.translate("MainWindow", u"ADDRESS LINE 2", None))
        self.txt_company_address.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Street address", None))
        self.txt_company_address2.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Apt, Suite, Unit\u2026", None))
        self.lbl_company_city.setText(QCoreApplication.translate("MainWindow", u"CITY", None))
        self.lbl_company_state.setText(QCoreApplication.translate("MainWindow", u"STATE", None))
        self.lbl_company_zip.setText(QCoreApplication.translate("MainWindow", u"ZIP CODE", None))
        self.txt_company_zip.setPlaceholderText(QCoreApplication.translate("MainWindow", u"00000-000", None))
        self.div_company_2.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color:#EEF2F7; border-radius:0px;", None))
        self.lbl_company_website.setText(QCoreApplication.translate("MainWindow", u"WEBSITE", None))
        self.lbl_company_status.setText(QCoreApplication.translate("MainWindow", u"STATUS", None))
        self.txt_company_website.setPlaceholderText(QCoreApplication.translate("MainWindow", u"https://\u2026", None))
        self.cmb_company_status.setItemText(0, QCoreApplication.translate("MainWindow", u"ACTIVE", None))
        self.cmb_company_status.setItemText(1, QCoreApplication.translate("MainWindow", u"INACTIVE", None))

        self.lbl_company_instagram.setText(QCoreApplication.translate("MainWindow", u"INSTAGRAM", None))
        self.lbl_company_facebook.setText(QCoreApplication.translate("MainWindow", u"FACEBOOK", None))
        self.lbl_company_linkedin.setText(QCoreApplication.translate("MainWindow", u"LINKEDIN", None))
        self.txt_company_instagram.setPlaceholderText(QCoreApplication.translate("MainWindow", u"@handle", None))
        self.txt_company_facebook.setPlaceholderText(QCoreApplication.translate("MainWindow", u"facebook.com/\u2026", None))
        self.txt_company_linkedin.setPlaceholderText(QCoreApplication.translate("MainWindow", u"linkedin.com/\u2026", None))
        self.lbl_company_twitter.setText(QCoreApplication.translate("MainWindow", u"TWITTER / X", None))
        self.lbl_company_notes.setText(QCoreApplication.translate("MainWindow", u"NOTES", None))
        self.txt_company_twitter.setPlaceholderText(QCoreApplication.translate("MainWindow", u"@handle", None))
        self.txt_company_notes.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Additional notes\u2026", None))
        self.frame_company_footer.setStyleSheet(QCoreApplication.translate("MainWindow", u"QFrame { background-color:#F8FAFD; border-top: 1px solid #EEF2F7; border-radius:0px; border-bottom-left-radius:8px; border-bottom-right-radius:8px; }", None))
        self.btn_delete_company.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.btn_save_company.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.tabWidget_companies_page.setTabText(self.tabWidget_companies_page.indexOf(self.tab_companies_master), QCoreApplication.translate("MainWindow", u"Companies", None))
        self.txt_search_contractors.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\U0001f50d  Search by name, company, city\U00002026", None))
        self.cmb_filter_contractor_status.setItemText(0, QCoreApplication.translate("MainWindow", u"All Status", None))
        self.cmb_filter_contractor_status.setItemText(1, QCoreApplication.translate("MainWindow", u"ACTIVE", None))
        self.cmb_filter_contractor_status.setItemText(2, QCoreApplication.translate("MainWindow", u"BLOCKED", None))
        self.cmb_filter_contractor_status.setItemText(3, QCoreApplication.translate("MainWindow", u"SUSPENDED", None))

        self.btn_refresh_contractors.setText(QCoreApplication.translate("MainWindow", u"\u21bb  Refresh", None))
        self.btn_export_excel_contractors.setText(QCoreApplication.translate("MainWindow", u"\u2913  Excel", None))
        self.btn_export_pdf_contractors.setText(QCoreApplication.translate("MainWindow", u"\u2913  PDF", None))
        self.btn_new_contractor.setText(QCoreApplication.translate("MainWindow", u"+  New Contractor", None))
        self.btn_toggle_contractors_table_expanded.setText(QCoreApplication.translate("MainWindow", u"\u26f6  Expand Table", None))
        ___qtablewidgetitem36 = self.table_contractors.horizontalHeaderItem(0)
        ___qtablewidgetitem36.setText(QCoreApplication.translate("MainWindow", u"ID", None))
        ___qtablewidgetitem37 = self.table_contractors.horizontalHeaderItem(1)
        ___qtablewidgetitem37.setText(QCoreApplication.translate("MainWindow", u"Full Name", None))
        ___qtablewidgetitem38 = self.table_contractors.horizontalHeaderItem(2)
        ___qtablewidgetitem38.setText(QCoreApplication.translate("MainWindow", u"Email", None))
        ___qtablewidgetitem39 = self.table_contractors.horizontalHeaderItem(3)
        ___qtablewidgetitem39.setText(QCoreApplication.translate("MainWindow", u"Phone", None))
        ___qtablewidgetitem40 = self.table_contractors.horizontalHeaderItem(4)
        ___qtablewidgetitem40.setText(QCoreApplication.translate("MainWindow", u"Position", None))
        ___qtablewidgetitem41 = self.table_contractors.horizontalHeaderItem(5)
        ___qtablewidgetitem41.setText(QCoreApplication.translate("MainWindow", u"Company Name", None))
        ___qtablewidgetitem42 = self.table_contractors.horizontalHeaderItem(6)
        ___qtablewidgetitem42.setText(QCoreApplication.translate("MainWindow", u"Company Phone", None))
        ___qtablewidgetitem43 = self.table_contractors.horizontalHeaderItem(7)
        ___qtablewidgetitem43.setText(QCoreApplication.translate("MainWindow", u"City", None))
        ___qtablewidgetitem44 = self.table_contractors.horizontalHeaderItem(8)
        ___qtablewidgetitem44.setText(QCoreApplication.translate("MainWindow", u"State", None))
        ___qtablewidgetitem45 = self.table_contractors.horizontalHeaderItem(9)
        ___qtablewidgetitem45.setText(QCoreApplication.translate("MainWindow", u"Status", None))
        self.lbl_contractor_form_title.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:15px; font-weight:700; color:#FFFFFF; background:transparent;", None))
        self.lbl_contractor_form_title.setText(QCoreApplication.translate("MainWindow", u"Contractor Record", None))
        self.lbl_contractor_id_display.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; color:#90B8E0; background:transparent;", None))
        self.lbl_contractor_id_display.setText(QCoreApplication.translate("MainWindow", u"#ID: \u2014", None))
        self.lbl_contractor_full_name.setText(QCoreApplication.translate("MainWindow", u"FULL NAME", None))
        self.lbl_contractor_position.setText(QCoreApplication.translate("MainWindow", u"POSITION", None))
        self.txt_contractor_full_name.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Full name\u2026", None))
        self.txt_contractor_position.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Role / position\u2026", None))
        self.lbl_contractor_email.setText(QCoreApplication.translate("MainWindow", u"EMAIL", None))
        self.lbl_contractor_phone.setText(QCoreApplication.translate("MainWindow", u"PHONE NUMBER", None))
        self.lbl_contractor_phone2.setText(QCoreApplication.translate("MainWindow", u"PHONE NUMBER 2", None))
        self.txt_contractor_email.setPlaceholderText(QCoreApplication.translate("MainWindow", u"email@example.com", None))
        self.txt_contractor_phone.setPlaceholderText(QCoreApplication.translate("MainWindow", u"(000) 000-0000", None))
        self.txt_contractor_phone2.setPlaceholderText(QCoreApplication.translate("MainWindow", u"(000) 000-0000", None))
        self.div_contractor_1.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color:#EEF2F7; border-radius:0px;", None))
        self.lbl_contractor_company_name.setText(QCoreApplication.translate("MainWindow", u"COMPANY NAME", None))
        self.lbl_contractor_company_email.setText(QCoreApplication.translate("MainWindow", u"COMPANY EMAIL", None))
        self.txt_contractor_company_name.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Company name\u2026", None))
        self.txt_contractor_company_email.setPlaceholderText(QCoreApplication.translate("MainWindow", u"email@company.com", None))
        self.lbl_contractor_company_phone.setText(QCoreApplication.translate("MainWindow", u"COMPANY PHONE", None))
        self.lbl_contractor_company_phone2.setText(QCoreApplication.translate("MainWindow", u"COMPANY PHONE 2", None))
        self.txt_contractor_company_phone.setPlaceholderText(QCoreApplication.translate("MainWindow", u"(000) 000-0000", None))
        self.txt_contractor_company_phone2.setPlaceholderText(QCoreApplication.translate("MainWindow", u"(000) 000-0000", None))
        self.div_contractor_2.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color:#EEF2F7; border-radius:0px;", None))
        self.lbl_contractor_address.setText(QCoreApplication.translate("MainWindow", u"ADDRESS", None))
        self.lbl_contractor_address2.setText(QCoreApplication.translate("MainWindow", u"ADDRESS LINE 2", None))
        self.txt_contractor_address.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Street address", None))
        self.txt_contractor_address2.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Apt, Suite, Unit\u2026", None))
        self.lbl_contractor_city.setText(QCoreApplication.translate("MainWindow", u"CITY", None))
        self.lbl_contractor_state.setText(QCoreApplication.translate("MainWindow", u"STATE", None))
        self.lbl_contractor_zip.setText(QCoreApplication.translate("MainWindow", u"ZIP CODE", None))
        self.txt_contractor_zip.setPlaceholderText(QCoreApplication.translate("MainWindow", u"00000-000", None))
        self.div_contractor_3.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color:#EEF2F7; border-radius:0px;", None))
        self.lbl_contractor_website.setText(QCoreApplication.translate("MainWindow", u"WEBSITE", None))
        self.lbl_contractor_status.setText(QCoreApplication.translate("MainWindow", u"STATUS", None))
        self.txt_contractor_website.setPlaceholderText(QCoreApplication.translate("MainWindow", u"https://\u2026", None))
        self.cmb_contractor_status.setItemText(0, QCoreApplication.translate("MainWindow", u"ACTIVE", None))
        self.cmb_contractor_status.setItemText(1, QCoreApplication.translate("MainWindow", u"BLOCKED", None))
        self.cmb_contractor_status.setItemText(2, QCoreApplication.translate("MainWindow", u"SUSPENDED", None))

        self.lbl_contractor_instagram.setText(QCoreApplication.translate("MainWindow", u"INSTAGRAM", None))
        self.lbl_contractor_facebook.setText(QCoreApplication.translate("MainWindow", u"FACEBOOK", None))
        self.lbl_contractor_linkedin.setText(QCoreApplication.translate("MainWindow", u"LINKEDIN", None))
        self.txt_contractor_instagram.setPlaceholderText(QCoreApplication.translate("MainWindow", u"@handle", None))
        self.txt_contractor_facebook.setPlaceholderText(QCoreApplication.translate("MainWindow", u"facebook.com/\u2026", None))
        self.txt_contractor_linkedin.setPlaceholderText(QCoreApplication.translate("MainWindow", u"linkedin.com/\u2026", None))
        self.lbl_contractor_twitter.setText(QCoreApplication.translate("MainWindow", u"TWITTER / X", None))
        self.lbl_contractor_notes.setText(QCoreApplication.translate("MainWindow", u"NOTES", None))
        self.txt_contractor_twitter.setPlaceholderText(QCoreApplication.translate("MainWindow", u"@handle", None))
        self.txt_contractor_notes.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Additional notes\u2026", None))
        self.lbl_contractor_payment_cycle_type.setText(QCoreApplication.translate("MainWindow", u"PAYMENT CYCLE", None))
        self.lbl_contractor_payment_cycle_weekday.setText(QCoreApplication.translate("MainWindow", u"PAYMENT DAY", None))
        self.lbl_contractor_payment_cycle_days.setText(QCoreApplication.translate("MainWindow", u"DAYS UNTIL DUE", None))
        self.cmb_contractor_payment_cycle_type.setItemText(0, QCoreApplication.translate("MainWindow", u"Weekly", None))
        self.cmb_contractor_payment_cycle_type.setItemText(1, QCoreApplication.translate("MainWindow", u"Biweekly", None))
        self.cmb_contractor_payment_cycle_type.setItemText(2, QCoreApplication.translate("MainWindow", u"Custom Days", None))

        self.cmb_contractor_payment_cycle_weekday.setItemText(0, QCoreApplication.translate("MainWindow", u"Sunday", None))
        self.cmb_contractor_payment_cycle_weekday.setItemText(1, QCoreApplication.translate("MainWindow", u"Monday", None))
        self.cmb_contractor_payment_cycle_weekday.setItemText(2, QCoreApplication.translate("MainWindow", u"Tuesday", None))
        self.cmb_contractor_payment_cycle_weekday.setItemText(3, QCoreApplication.translate("MainWindow", u"Wednesday", None))
        self.cmb_contractor_payment_cycle_weekday.setItemText(4, QCoreApplication.translate("MainWindow", u"Thursday", None))
        self.cmb_contractor_payment_cycle_weekday.setItemText(5, QCoreApplication.translate("MainWindow", u"Friday", None))
        self.cmb_contractor_payment_cycle_weekday.setItemText(6, QCoreApplication.translate("MainWindow", u"Saturday", None))

        self.frame_contractor_footer.setStyleSheet(QCoreApplication.translate("MainWindow", u"QFrame { background-color:#F8FAFD; border-top: 1px solid #EEF2F7; border-radius:0px; border-bottom-left-radius:8px; border-bottom-right-radius:8px; }", None))
        self.btn_delete_contractor.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.btn_save_contractor.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.tabWidget_contractors_page.setTabText(self.tabWidget_contractors_page.indexOf(self.tab_contractors_master), QCoreApplication.translate("MainWindow", u"Contractors", None))
        self.txt_search_work_types.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\U0001f50d  Search by name\U00002026", None))
        self.cmb_filter_work_type_category.setItemText(0, QCoreApplication.translate("MainWindow", u"All Categories", None))
        self.cmb_filter_work_type_category.setItemText(1, QCoreApplication.translate("MainWindow", u"DEMOLITION", None))
        self.cmb_filter_work_type_category.setItemText(2, QCoreApplication.translate("MainWindow", u"INSTALLATION", None))
        self.cmb_filter_work_type_category.setItemText(3, QCoreApplication.translate("MainWindow", u"PREPARATION", None))
        self.cmb_filter_work_type_category.setItemText(4, QCoreApplication.translate("MainWindow", u"OTHERS", None))
        self.cmb_filter_work_type_category.setItemText(5, QCoreApplication.translate("MainWindow", u"REPARO", None))

        self.btn_refresh_work_types.setText(QCoreApplication.translate("MainWindow", u"\u21bb  Refresh", None))
        self.btn_export_excel_work_types.setText(QCoreApplication.translate("MainWindow", u"\u2913  Excel", None))
        self.btn_export_pdf_work_types.setText(QCoreApplication.translate("MainWindow", u"\u2913  PDF", None))
        self.btn_new_work_type.setText(QCoreApplication.translate("MainWindow", u"+  New Type", None))
        self.btn_toggle_work_types_table_expanded.setText(QCoreApplication.translate("MainWindow", u"\u26f6  Expand Table", None))
        ___qtablewidgetitem46 = self.table_work_types.horizontalHeaderItem(0)
        ___qtablewidgetitem46.setText(QCoreApplication.translate("MainWindow", u"ID", None))
        ___qtablewidgetitem47 = self.table_work_types.horizontalHeaderItem(1)
        ___qtablewidgetitem47.setText(QCoreApplication.translate("MainWindow", u"Category", None))
        ___qtablewidgetitem48 = self.table_work_types.horizontalHeaderItem(2)
        ___qtablewidgetitem48.setText(QCoreApplication.translate("MainWindow", u"Name", None))
        ___qtablewidgetitem49 = self.table_work_types.horizontalHeaderItem(3)
        ___qtablewidgetitem49.setText(QCoreApplication.translate("MainWindow", u"Unit", None))
        self.lbl_work_type_form_title.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:15px; font-weight:700; color:#FFFFFF; background:transparent;", None))
        self.lbl_work_type_form_title.setText(QCoreApplication.translate("MainWindow", u"Work Type Record", None))
        self.lbl_work_type_id_display.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; color:#90B8E0; background:transparent;", None))
        self.lbl_work_type_id_display.setText(QCoreApplication.translate("MainWindow", u"#ID: \u2014", None))
        self.txt_work_type_name.setPlaceholderText(QCoreApplication.translate("MainWindow", u"e.g. Carpet, Tile, Plywood\u2026", None))
        self.lbl_work_type_name.setText(QCoreApplication.translate("MainWindow", u"NAME", None))
        self.cmb_work_type_category.setItemText(0, QCoreApplication.translate("MainWindow", u"DEMOLITION", None))
        self.cmb_work_type_category.setItemText(1, QCoreApplication.translate("MainWindow", u"INSTALLATION", None))
        self.cmb_work_type_category.setItemText(2, QCoreApplication.translate("MainWindow", u"PREPARATION", None))
        self.cmb_work_type_category.setItemText(3, QCoreApplication.translate("MainWindow", u"OTHERS", None))
        self.cmb_work_type_category.setItemText(4, QCoreApplication.translate("MainWindow", u"REPARO", None))

        self.txt_work_type_unit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"PCS, SQFT, LFT\u2026", None))
        self.lbl_work_type_category.setText(QCoreApplication.translate("MainWindow", u"CATEGORY", None))
        self.lbl_work_type_unit.setText(QCoreApplication.translate("MainWindow", u"UNIT", None))
        self.frame_work_type_footer.setStyleSheet(QCoreApplication.translate("MainWindow", u"QFrame { background-color:#F8FAFD; border-top: 1px solid #EEF2F7; border-radius:0px; border-bottom-left-radius:8px; border-bottom-right-radius:8px; }", None))
        self.btn_delete_work_type.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.btn_save_work_type.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.tabWidget_work_types_page.setTabText(self.tabWidget_work_types_page.indexOf(self.tab_work_types_master), QCoreApplication.translate("MainWindow", u"Work Types", None))
        self.lbl_receivables_total_icon.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:20px; background:transparent;", None))
        self.lbl_receivables_total_icon.setText(QCoreApplication.translate("MainWindow", u"\U0001f4b0", None))
        self.lbl_receivables_total_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:24px; font-weight:800; color:#1A1F36; background:transparent;", None))
        self.lbl_receivables_total_value.setText(QCoreApplication.translate("MainWindow", u"$0.00", None))
        self.lbl_receivables_total_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_receivables_total_label.setText(QCoreApplication.translate("MainWindow", u"Total Receivable", None))
        self.lbl_receivables_month_icon.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:20px; background:transparent;", None))
        self.lbl_receivables_month_icon.setText(QCoreApplication.translate("MainWindow", u"\u2705", None))
        self.lbl_receivables_month_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:24px; font-weight:800; color:#1A1F36; background:transparent;", None))
        self.lbl_receivables_month_value.setText(QCoreApplication.translate("MainWindow", u"$0.00", None))
        self.lbl_receivables_month_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_receivables_month_label.setText(QCoreApplication.translate("MainWindow", u"Received This Month", None))
        self.lbl_receivables_open_icon.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:20px; background:transparent;", None))
        self.lbl_receivables_open_icon.setText(QCoreApplication.translate("MainWindow", u"\U0001f477", None))
        self.lbl_receivables_open_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:24px; font-weight:800; color:#1A1F36; background:transparent;", None))
        self.lbl_receivables_open_value.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.lbl_receivables_open_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_receivables_open_label.setText(QCoreApplication.translate("MainWindow", u"Contractors/Companies/Clients With Open Balance", None))
        self.lbl_receivables_overdue_icon.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:20px; background:transparent;", None))
        self.lbl_receivables_overdue_icon.setText(QCoreApplication.translate("MainWindow", u"\u26a0\ufe0f", None))
        self.lbl_receivables_overdue_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:24px; font-weight:800; color:#C62828; background:transparent;", None))
        self.lbl_receivables_overdue_value.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.lbl_receivables_overdue_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_receivables_overdue_label.setText(QCoreApplication.translate("MainWindow", u"Overdue (30+ days)", None))
        self.lbl_dashboard_period.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_dashboard_period.setText(QCoreApplication.translate("MainWindow", u"Period:", None))
        ___qtablewidgetitem50 = self.table_receivables_breakdown.horizontalHeaderItem(0)
        ___qtablewidgetitem50.setText(QCoreApplication.translate("MainWindow", u"Type", None))
        ___qtablewidgetitem51 = self.table_receivables_breakdown.horizontalHeaderItem(1)
        ___qtablewidgetitem51.setText(QCoreApplication.translate("MainWindow", u"Name", None))
        ___qtablewidgetitem52 = self.table_receivables_breakdown.horizontalHeaderItem(2)
        ___qtablewidgetitem52.setText(QCoreApplication.translate("MainWindow", u"Total Billed", None))
        ___qtablewidgetitem53 = self.table_receivables_breakdown.horizontalHeaderItem(3)
        ___qtablewidgetitem53.setText(QCoreApplication.translate("MainWindow", u"Received", None))
        ___qtablewidgetitem54 = self.table_receivables_breakdown.horizontalHeaderItem(4)
        ___qtablewidgetitem54.setText(QCoreApplication.translate("MainWindow", u"Pending", None))
        self.btn_dashboard_record_payment.setText(QCoreApplication.translate("MainWindow", u"\U0001f4b3  Record Payment", None))
        self.lbl_dashboard_aging_title.setText(QCoreApplication.translate("MainWindow", u"Aging Report (open balance)", None))
        self.lbl_aging_0_30_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:18px; font-weight:800; color:#2E7D32; background:transparent;", None))
        self.lbl_aging_0_30_value.setText(QCoreApplication.translate("MainWindow", u"$0.00", None))
        self.lbl_aging_0_30_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_aging_0_30_label.setText(QCoreApplication.translate("MainWindow", u"0-30 days", None))
        self.lbl_aging_31_60_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:18px; font-weight:800; color:#E65100; background:transparent;", None))
        self.lbl_aging_31_60_value.setText(QCoreApplication.translate("MainWindow", u"$0.00", None))
        self.lbl_aging_31_60_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_aging_31_60_label.setText(QCoreApplication.translate("MainWindow", u"31-60 days", None))
        self.lbl_aging_61_90_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:18px; font-weight:800; color:#C62828; background:transparent;", None))
        self.lbl_aging_61_90_value.setText(QCoreApplication.translate("MainWindow", u"$0.00", None))
        self.lbl_aging_61_90_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_aging_61_90_label.setText(QCoreApplication.translate("MainWindow", u"61-90 days", None))
        self.lbl_aging_90_plus_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:18px; font-weight:800; color:#B71C1C; background:transparent;", None))
        self.lbl_aging_90_plus_value.setText(QCoreApplication.translate("MainWindow", u"$0.00", None))
        self.lbl_aging_90_plus_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_aging_90_plus_label.setText(QCoreApplication.translate("MainWindow", u"90+ days", None))
        self.lbl_dashboard_chart_title.setText(QCoreApplication.translate("MainWindow", u"Received \u2014 Last 6 Months", None))
        self.lbl_dashboard_payment_method_title.setText(QCoreApplication.translate("MainWindow", u"Received by Payment Method", None))
        ___qtablewidgetitem55 = self.table_dashboard_payment_methods.horizontalHeaderItem(0)
        ___qtablewidgetitem55.setText(QCoreApplication.translate("MainWindow", u"Method", None))
        ___qtablewidgetitem56 = self.table_dashboard_payment_methods.horizontalHeaderItem(1)
        ___qtablewidgetitem56.setText(QCoreApplication.translate("MainWindow", u"Amount Received", None))
        self.lbl_dashboard_debtors_title.setText(QCoreApplication.translate("MainWindow", u"Top Debtors", None))
        ___qtablewidgetitem57 = self.table_dashboard_top_debtors.horizontalHeaderItem(0)
        ___qtablewidgetitem57.setText(QCoreApplication.translate("MainWindow", u"Type", None))
        ___qtablewidgetitem58 = self.table_dashboard_top_debtors.horizontalHeaderItem(1)
        ___qtablewidgetitem58.setText(QCoreApplication.translate("MainWindow", u"Name", None))
        ___qtablewidgetitem59 = self.table_dashboard_top_debtors.horizontalHeaderItem(2)
        ___qtablewidgetitem59.setText(QCoreApplication.translate("MainWindow", u"Amount Owed", None))
        self.tabWidget_receivables.setTabText(self.tabWidget_receivables.indexOf(self.tab_receivables_dashboard), QCoreApplication.translate("MainWindow", u"Dashboard", None))
        self.cmb_invoice_entity_type.setItemText(0, QCoreApplication.translate("MainWindow", u"Contractor", None))
        self.cmb_invoice_entity_type.setItemText(1, QCoreApplication.translate("MainWindow", u"Company", None))
        self.cmb_invoice_entity_type.setItemText(2, QCoreApplication.translate("MainWindow", u"Client", None))

        self.cmb_filter_invoice_status.setItemText(0, QCoreApplication.translate("MainWindow", u"All Status", None))
        self.cmb_filter_invoice_status.setItemText(1, QCoreApplication.translate("MainWindow", u"PENDING", None))
        self.cmb_filter_invoice_status.setItemText(2, QCoreApplication.translate("MainWindow", u"PARTIAL", None))
        self.cmb_filter_invoice_status.setItemText(3, QCoreApplication.translate("MainWindow", u"RECEIVED", None))

        self.btn_refresh_invoices.setText(QCoreApplication.translate("MainWindow", u"\u21bb  Refresh", None))
        self.btn_export_excel_invoices.setText(QCoreApplication.translate("MainWindow", u"\u2913  Excel", None))
        self.btn_export_pdf_invoices.setText(QCoreApplication.translate("MainWindow", u"\u2913  PDF", None))
#if QT_CONFIG(tooltip)
        self.btn_generate_invoices.setToolTip(QCoreApplication.translate("MainWindow", u"Generate PDF invoices to send to contractors, companies or clients, by date range", None))
#endif // QT_CONFIG(tooltip)
        self.btn_generate_invoices.setText(QCoreApplication.translate("MainWindow", u"\U0001f9fe  Generate Invoices", None))
#if QT_CONFIG(tooltip)
        self.btn_send_selected_invoices.setToolTip(QCoreApplication.translate("MainWindow", u"Send the checked invoices by Email or WhatsApp", None))
#endif // QT_CONFIG(tooltip)
        self.btn_send_selected_invoices.setText(QCoreApplication.translate("MainWindow", u"\U0001f4e4  Send Selected", None))
        ___qtablewidgetitem60 = self.table_contractor_invoices.horizontalHeaderItem(0)
        ___qtablewidgetitem60.setText(QCoreApplication.translate("MainWindow", u"ID", None))
        ___qtablewidgetitem61 = self.table_contractor_invoices.horizontalHeaderItem(1)
        ___qtablewidgetitem61.setText(QCoreApplication.translate("MainWindow", u"Entity", None))
        ___qtablewidgetitem62 = self.table_contractor_invoices.horizontalHeaderItem(2)
        ___qtablewidgetitem62.setText(QCoreApplication.translate("MainWindow", u"Period From", None))
        ___qtablewidgetitem63 = self.table_contractor_invoices.horizontalHeaderItem(3)
        ___qtablewidgetitem63.setText(QCoreApplication.translate("MainWindow", u"Period To", None))
        ___qtablewidgetitem64 = self.table_contractor_invoices.horizontalHeaderItem(4)
        ___qtablewidgetitem64.setText(QCoreApplication.translate("MainWindow", u"Jobs + Expenses", None))
        ___qtablewidgetitem65 = self.table_contractor_invoices.horizontalHeaderItem(5)
        ___qtablewidgetitem65.setText(QCoreApplication.translate("MainWindow", u"Total", None))
        ___qtablewidgetitem66 = self.table_contractor_invoices.horizontalHeaderItem(6)
        ___qtablewidgetitem66.setText(QCoreApplication.translate("MainWindow", u"Paid", None))
        ___qtablewidgetitem67 = self.table_contractor_invoices.horizontalHeaderItem(7)
        ___qtablewidgetitem67.setText(QCoreApplication.translate("MainWindow", u"Status", None))
        ___qtablewidgetitem68 = self.table_contractor_invoices.horizontalHeaderItem(8)
        ___qtablewidgetitem68.setText(QCoreApplication.translate("MainWindow", u"Select", None))
        self.lbl_invoices_hint.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:11px; color:#8A94A6; background:transparent;", None))
        self.lbl_invoices_hint.setText(QCoreApplication.translate("MainWindow", u"Double-click a row to view details, mark as received, or record a partial payment.", None))
        self.tabWidget_receivables.setTabText(self.tabWidget_receivables.indexOf(self.tab_receivables_invoices), QCoreApplication.translate("MainWindow", u"Invoices", None))
        self.txt_search_expenses.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\U0001f50d  Search by description\U00002026", None))
        self.cmb_filter_expense_category.setItemText(0, QCoreApplication.translate("MainWindow", u"All Categories", None))
        self.cmb_filter_expense_category.setItemText(1, QCoreApplication.translate("MainWindow", u"MATERIALS", None))
        self.cmb_filter_expense_category.setItemText(2, QCoreApplication.translate("MainWindow", u"GAS", None))
        self.cmb_filter_expense_category.setItemText(3, QCoreApplication.translate("MainWindow", u"TOOLS", None))
        self.cmb_filter_expense_category.setItemText(4, QCoreApplication.translate("MainWindow", u"OTHER", None))

        self.btn_refresh_expenses.setText(QCoreApplication.translate("MainWindow", u"\u21bb  Refresh", None))
        self.btn_export_excel_expenses.setText(QCoreApplication.translate("MainWindow", u"\u2913  Excel", None))
        self.btn_export_pdf_expenses.setText(QCoreApplication.translate("MainWindow", u"\u2913  PDF", None))
        self.btn_new_expense.setText(QCoreApplication.translate("MainWindow", u"+  New Expense", None))
        self.btn_toggle_expenses_table_expanded.setText(QCoreApplication.translate("MainWindow", u"\u26f6  Expand Table", None))
        ___qtablewidgetitem69 = self.table_expenses.horizontalHeaderItem(0)
        ___qtablewidgetitem69.setText(QCoreApplication.translate("MainWindow", u"ID", None))
        ___qtablewidgetitem70 = self.table_expenses.horizontalHeaderItem(1)
        ___qtablewidgetitem70.setText(QCoreApplication.translate("MainWindow", u"Date", None))
        ___qtablewidgetitem71 = self.table_expenses.horizontalHeaderItem(2)
        ___qtablewidgetitem71.setText(QCoreApplication.translate("MainWindow", u"Category", None))
        ___qtablewidgetitem72 = self.table_expenses.horizontalHeaderItem(3)
        ___qtablewidgetitem72.setText(QCoreApplication.translate("MainWindow", u"Description", None))
        ___qtablewidgetitem73 = self.table_expenses.horizontalHeaderItem(4)
        ___qtablewidgetitem73.setText(QCoreApplication.translate("MainWindow", u"Amount", None))
        ___qtablewidgetitem74 = self.table_expenses.horizontalHeaderItem(5)
        ___qtablewidgetitem74.setText(QCoreApplication.translate("MainWindow", u"Contractor", None))
        ___qtablewidgetitem75 = self.table_expenses.horizontalHeaderItem(6)
        ___qtablewidgetitem75.setText(QCoreApplication.translate("MainWindow", u"Submitted By", None))
        self.lbl_expense_form_title.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:15px; font-weight:700; color:#FFFFFF; background:transparent;", None))
        self.lbl_expense_form_title.setText(QCoreApplication.translate("MainWindow", u"Expense Record", None))
        self.lbl_expense_id_display.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; color:#90B8E0; background:transparent;", None))
        self.lbl_expense_id_display.setText(QCoreApplication.translate("MainWindow", u"#ID: \u2014", None))
        self.lbl_expense_date.setText(QCoreApplication.translate("MainWindow", u"DATE", None))
        self.lbl_expense_category.setText(QCoreApplication.translate("MainWindow", u"CATEGORY", None))
        self.date_expense.setDisplayFormat(QCoreApplication.translate("MainWindow", u"MM/dd/yyyy", None))
        self.cmb_expense_category.setItemText(0, QCoreApplication.translate("MainWindow", u"MATERIALS", None))
        self.cmb_expense_category.setItemText(1, QCoreApplication.translate("MainWindow", u"GAS", None))
        self.cmb_expense_category.setItemText(2, QCoreApplication.translate("MainWindow", u"TOOLS", None))
        self.cmb_expense_category.setItemText(3, QCoreApplication.translate("MainWindow", u"OTHER", None))

        self.lbl_expense_description.setText(QCoreApplication.translate("MainWindow", u"DESCRIPTION", None))
        self.txt_expense_description.setPlaceholderText(QCoreApplication.translate("MainWindow", u"e.g. Vinyl planks, gas for the truck\u2026", None))
        self.lbl_expense_vendor.setText(QCoreApplication.translate("MainWindow", u"VENDOR / STORE", None))
        self.cmb_expense_vendor.setProperty(u"placeholderText", QCoreApplication.translate("MainWindow", u"e.g. Home Depot, Lowe's, Shell Gas Station\u2026", None))
        self.lbl_expense_amount.setText(QCoreApplication.translate("MainWindow", u"AMOUNT ($)", None))
        self.lbl_expense_submitted_by.setText(QCoreApplication.translate("MainWindow", u"PAYABLE / RECEIVABLE", None))
        self.dspn_expense_amount.setPrefix(QCoreApplication.translate("MainWindow", u"$ ", None))
        self.cmb_expense_submitted_by.setItemText(0, QCoreApplication.translate("MainWindow", u"Payable", None))
        self.cmb_expense_submitted_by.setItemText(1, QCoreApplication.translate("MainWindow", u"Receivable", None))

        self.lbl_expense_entity_type.setText(QCoreApplication.translate("MainWindow", u"TYPE", None))
        self.lbl_expense_contractor.setText(QCoreApplication.translate("MainWindow", u"NAME (OPTIONAL)", None))
        self.cmb_expense_entity_type.setItemText(0, QCoreApplication.translate("MainWindow", u"Contractor", None))
        self.cmb_expense_entity_type.setItemText(1, QCoreApplication.translate("MainWindow", u"Company", None))
        self.cmb_expense_entity_type.setItemText(2, QCoreApplication.translate("MainWindow", u"Client", None))
        self.cmb_expense_entity_type.setItemText(3, QCoreApplication.translate("MainWindow", u"Others", None))

        self.lbl_expense_receipt.setText(QCoreApplication.translate("MainWindow", u"RECEIPT (OPTIONAL)", None))
        self.txt_expense_receipt_path.setPlaceholderText(QCoreApplication.translate("MainWindow", u"No file attached\u2026", None))
        self.btn_expense_attach_receipt.setText(QCoreApplication.translate("MainWindow", u"\U0001f4ce Attach File\U00002026", None))
        self.frame_expense_footer.setStyleSheet(QCoreApplication.translate("MainWindow", u"QFrame { background-color:#F8FAFD; border-top: 1px solid #EEF2F7; border-radius:0px; border-bottom-left-radius:8px; border-bottom-right-radius:8px; }", None))
        self.btn_delete_expense.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.btn_save_expense.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.tabWidget_receivables.setTabText(self.tabWidget_receivables.indexOf(self.tab_expenses_master), QCoreApplication.translate("MainWindow", u"Expenses", None))
        self.lbl_pnl_period.setText(QCoreApplication.translate("MainWindow", u"Period:", None))
        self.btn_export_pdf_pnl.setText(QCoreApplication.translate("MainWindow", u"\u2913  Export PDF", None))
        self.lbl_pnl_revenue_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:22px; font-weight:800; color:#2E7D32; background:transparent;", None))
        self.lbl_pnl_revenue_value.setText(QCoreApplication.translate("MainWindow", u"$0.00", None))
        self.lbl_pnl_revenue_label.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; font-weight:600; color:#6B7C93; background:transparent;", None))
        self.lbl_pnl_revenue_label.setText(QCoreApplication.translate("MainWindow", u"Revenue (received in period)", None))
        self.lbl_pnl_expenses_title.setText(QCoreApplication.translate("MainWindow", u"Expenses by Category", None))
        ___qtablewidgetitem76 = self.table_pnl_expenses.horizontalHeaderItem(0)
        ___qtablewidgetitem76.setText(QCoreApplication.translate("MainWindow", u"Category", None))
        ___qtablewidgetitem77 = self.table_pnl_expenses.horizontalHeaderItem(1)
        ___qtablewidgetitem77.setText(QCoreApplication.translate("MainWindow", u"Amount", None))
        self.lbl_pnl_total_expenses_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:14px; font-weight:700; color:#C62828; background:transparent;", None))
        self.lbl_pnl_total_expenses_value.setText(QCoreApplication.translate("MainWindow", u"Total Expenses: $0.00", None))
        self.lbl_pnl_net_profit_value.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:22px; font-weight:800; color:#1565C0; background:transparent;", None))
        self.lbl_pnl_net_profit_value.setText(QCoreApplication.translate("MainWindow", u"Net Profit: $0.00", None))
        self.tabWidget_receivables.setTabText(self.tabWidget_receivables.indexOf(self.tab_pnl), QCoreApplication.translate("MainWindow", u"P&L", None))
        self.lbl_1099_year.setText(QCoreApplication.translate("MainWindow", u"Tax Year:", None))
        self.btn_export_pdf_1099.setText(QCoreApplication.translate("MainWindow", u"\u2913  Export PDF", None))
        self.btn_export_excel_1099.setText(QCoreApplication.translate("MainWindow", u"\u2913  Export Excel", None))
        self.lbl_1099_note.setText(QCoreApplication.translate("MainWindow", u"Contractors paid $600 or more in the selected year require a 1099-NEC (IRS threshold). This report is for your records \u2014 it does not file the form for you.", None))
        ___qtablewidgetitem78 = self.table_1099.horizontalHeaderItem(0)
        ___qtablewidgetitem78.setText(QCoreApplication.translate("MainWindow", u"Contractor", None))
        ___qtablewidgetitem79 = self.table_1099.horizontalHeaderItem(1)
        ___qtablewidgetitem79.setText(QCoreApplication.translate("MainWindow", u"Address", None))
        ___qtablewidgetitem80 = self.table_1099.horizontalHeaderItem(2)
        ___qtablewidgetitem80.setText(QCoreApplication.translate("MainWindow", u"City / State", None))
        ___qtablewidgetitem81 = self.table_1099.horizontalHeaderItem(3)
        ___qtablewidgetitem81.setText(QCoreApplication.translate("MainWindow", u"Total Paid", None))
        ___qtablewidgetitem82 = self.table_1099.horizontalHeaderItem(4)
        ___qtablewidgetitem82.setText(QCoreApplication.translate("MainWindow", u"1099 Required?", None))
        self.lbl_1099_summary.setText(QCoreApplication.translate("MainWindow", u"0 contractor(s) require a 1099 this year.", None))
        self.tabWidget_receivables.setTabText(self.tabWidget_receivables.indexOf(self.tab_1099), QCoreApplication.translate("MainWindow", u"1099 Report", None))
        self.lbl_sales_summary_period.setText(QCoreApplication.translate("MainWindow", u"Period:", None))
        self.lbl_sales_summary_type.setText(QCoreApplication.translate("MainWindow", u"Type:", None))
        self.cmb_sales_summary_type.setItemText(0, QCoreApplication.translate("MainWindow", u"All", None))
        self.cmb_sales_summary_type.setItemText(1, QCoreApplication.translate("MainWindow", u"Contractor", None))
        self.cmb_sales_summary_type.setItemText(2, QCoreApplication.translate("MainWindow", u"Company", None))
        self.cmb_sales_summary_type.setItemText(3, QCoreApplication.translate("MainWindow", u"Client", None))

        self.btn_export_pdf_sales_summary.setText(QCoreApplication.translate("MainWindow", u"\u2913  Export PDF", None))
        ___qtablewidgetitem83 = self.table_sales_summary.horizontalHeaderItem(0)
        ___qtablewidgetitem83.setText(QCoreApplication.translate("MainWindow", u"Rank", None))
        ___qtablewidgetitem84 = self.table_sales_summary.horizontalHeaderItem(1)
        ___qtablewidgetitem84.setText(QCoreApplication.translate("MainWindow", u"Type", None))
        ___qtablewidgetitem85 = self.table_sales_summary.horizontalHeaderItem(2)
        ___qtablewidgetitem85.setText(QCoreApplication.translate("MainWindow", u"Name", None))
        ___qtablewidgetitem86 = self.table_sales_summary.horizontalHeaderItem(3)
        ___qtablewidgetitem86.setText(QCoreApplication.translate("MainWindow", u"Total Billed", None))
        ___qtablewidgetitem87 = self.table_sales_summary.horizontalHeaderItem(4)
        ___qtablewidgetitem87.setText(QCoreApplication.translate("MainWindow", u"Total Received", None))
        ___qtablewidgetitem88 = self.table_sales_summary.horizontalHeaderItem(5)
        ___qtablewidgetitem88.setText(QCoreApplication.translate("MainWindow", u"Open Balance", None))
        self.lbl_sales_summary_total.setText(QCoreApplication.translate("MainWindow", u"Total Received: $0.00", None))
        self.tabWidget_receivables.setTabText(self.tabWidget_receivables.indexOf(self.tab_sales_summary), QCoreApplication.translate("MainWindow", u"Sales Summary", None))
        self.txt_search_customers.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\U0001f50d  Search by name, email, phone\U00002026", None))
        self.btn_refresh_customers.setText(QCoreApplication.translate("MainWindow", u"\u21bb  Refresh", None))
        self.btn_export_excel_customers.setText(QCoreApplication.translate("MainWindow", u"\u2913  Excel", None))
        self.btn_export_pdf_customers.setText(QCoreApplication.translate("MainWindow", u"\u2913  PDF", None))
        self.btn_new_customer.setText(QCoreApplication.translate("MainWindow", u"+  New Customer", None))
        self.btn_toggle_customers_table_expanded.setText(QCoreApplication.translate("MainWindow", u"\u26f6  Expand Table", None))
        ___qtablewidgetitem89 = self.table_customers.horizontalHeaderItem(0)
        ___qtablewidgetitem89.setText(QCoreApplication.translate("MainWindow", u"ID", None))
        ___qtablewidgetitem90 = self.table_customers.horizontalHeaderItem(1)
        ___qtablewidgetitem90.setText(QCoreApplication.translate("MainWindow", u"Full Name", None))
        ___qtablewidgetitem91 = self.table_customers.horizontalHeaderItem(2)
        ___qtablewidgetitem91.setText(QCoreApplication.translate("MainWindow", u"Email", None))
        ___qtablewidgetitem92 = self.table_customers.horizontalHeaderItem(3)
        ___qtablewidgetitem92.setText(QCoreApplication.translate("MainWindow", u"Phone", None))
        ___qtablewidgetitem93 = self.table_customers.horizontalHeaderItem(4)
        ___qtablewidgetitem93.setText(QCoreApplication.translate("MainWindow", u"City", None))
        ___qtablewidgetitem94 = self.table_customers.horizontalHeaderItem(5)
        ___qtablewidgetitem94.setText(QCoreApplication.translate("MainWindow", u"State", None))
        self.lbl_customer_form_title.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:15px; font-weight:700; color:#FFFFFF; background:transparent;", None))
        self.lbl_customer_form_title.setText(QCoreApplication.translate("MainWindow", u"Customer Record", None))
        self.lbl_customer_id_display.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; color:#90B8E0; background:transparent;", None))
        self.lbl_customer_id_display.setText(QCoreApplication.translate("MainWindow", u"#ID: \u2014", None))
        self.txt_customer_zip.setPlaceholderText(QCoreApplication.translate("MainWindow", u"00000-000", None))
        self.lbl_customer_city.setText(QCoreApplication.translate("MainWindow", u"CITY", None))
        self.txt_customer_address2.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Apt, Suite, Unit\u2026", None))
        self.txt_customer_address.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Street address\u2026", None))
        self.lbl_customer_state.setText(QCoreApplication.translate("MainWindow", u"STATE", None))
        self.lbl_customer_address.setText(QCoreApplication.translate("MainWindow", u"ADDRESS", None))
        self.lbl_customer_name.setText(QCoreApplication.translate("MainWindow", u"FULL NAME", None))
        self.lbl_customer_email.setText(QCoreApplication.translate("MainWindow", u"EMAIL", None))
        self.txt_customer_name.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Full name\u2026", None))
        self.txt_customer_email.setPlaceholderText(QCoreApplication.translate("MainWindow", u"email@example.com", None))
        self.lbl_customer_phone.setText(QCoreApplication.translate("MainWindow", u"PHONE", None))
        self.txt_customer_phone.setPlaceholderText(QCoreApplication.translate("MainWindow", u"(000) 000-0000", None))
        self.lbl_customer_zip.setText(QCoreApplication.translate("MainWindow", u"ZIP CODE", None))
        self.txt_customer_phone2.setPlaceholderText(QCoreApplication.translate("MainWindow", u"(000) 000-0000", None))
        self.lbl_customer_phone2.setText(QCoreApplication.translate("MainWindow", u"PHONE 2", None))
        self.lbl_customer_job_history_title.setText(QCoreApplication.translate("MainWindow", u"Job History", None))
        ___qtablewidgetitem95 = self.table_customer_job_history.horizontalHeaderItem(0)
        ___qtablewidgetitem95.setText(QCoreApplication.translate("MainWindow", u"Date", None))
        ___qtablewidgetitem96 = self.table_customer_job_history.horizontalHeaderItem(1)
        ___qtablewidgetitem96.setText(QCoreApplication.translate("MainWindow", u"Contractor", None))
        ___qtablewidgetitem97 = self.table_customer_job_history.horizontalHeaderItem(2)
        ___qtablewidgetitem97.setText(QCoreApplication.translate("MainWindow", u"Company", None))
        ___qtablewidgetitem98 = self.table_customer_job_history.horizontalHeaderItem(3)
        ___qtablewidgetitem98.setText(QCoreApplication.translate("MainWindow", u"Address", None))
        ___qtablewidgetitem99 = self.table_customer_job_history.horizontalHeaderItem(4)
        ___qtablewidgetitem99.setText(QCoreApplication.translate("MainWindow", u"Value", None))
        ___qtablewidgetitem100 = self.table_customer_job_history.horizontalHeaderItem(5)
        ___qtablewidgetitem100.setText(QCoreApplication.translate("MainWindow", u"Status", None))
        self.lbl_customer_job_history_total.setText(QCoreApplication.translate("MainWindow", u"Total: $0.00", None))
        self.frame_customer_footer.setStyleSheet(QCoreApplication.translate("MainWindow", u"QFrame { background-color:#F8FAFD; border-top: 1px solid #EEF2F7; border-radius:0px; border-bottom-left-radius:8px; border-bottom-right-radius:8px; }", None))
        self.btn_delete_customer.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.btn_save_customer.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.txt_search_users.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\U0001f50d  Search by name, username, email\U00002026", None))
        self.cmb_filter_user_status.setItemText(0, QCoreApplication.translate("MainWindow", u"All Status", None))
        self.cmb_filter_user_status.setItemText(1, QCoreApplication.translate("MainWindow", u"Active", None))
        self.cmb_filter_user_status.setItemText(2, QCoreApplication.translate("MainWindow", u"Inactive", None))
        self.cmb_filter_user_status.setItemText(3, QCoreApplication.translate("MainWindow", u"Suspended", None))

        self.btn_refresh_users.setText(QCoreApplication.translate("MainWindow", u"\u21bb  Refresh", None))
        self.btn_export_excel_users.setText(QCoreApplication.translate("MainWindow", u"\u2913  Excel", None))
        self.btn_export_pdf_users.setText(QCoreApplication.translate("MainWindow", u"\u2913  PDF", None))
#if QT_CONFIG(tooltip)
        self.btn_update_user.setToolTip(QCoreApplication.translate("MainWindow", u"Load selected user into the edit form", None))
#endif // QT_CONFIG(tooltip)
        self.btn_update_user.setText(QCoreApplication.translate("MainWindow", u"\u270e  Update", None))
        self.btn_new_user.setText(QCoreApplication.translate("MainWindow", u"+  New User", None))
        self.btn_toggle_users_table_expanded.setText(QCoreApplication.translate("MainWindow", u"\u26f6  Expand Table", None))
        ___qtablewidgetitem101 = self.table_users.horizontalHeaderItem(0)
        ___qtablewidgetitem101.setText(QCoreApplication.translate("MainWindow", u"ID", None))
        ___qtablewidgetitem102 = self.table_users.horizontalHeaderItem(1)
        ___qtablewidgetitem102.setText(QCoreApplication.translate("MainWindow", u"Full Name", None))
        ___qtablewidgetitem103 = self.table_users.horizontalHeaderItem(2)
        ___qtablewidgetitem103.setText(QCoreApplication.translate("MainWindow", u"Email", None))
        ___qtablewidgetitem104 = self.table_users.horizontalHeaderItem(3)
        ___qtablewidgetitem104.setText(QCoreApplication.translate("MainWindow", u"Phone", None))
        ___qtablewidgetitem105 = self.table_users.horizontalHeaderItem(4)
        ___qtablewidgetitem105.setText(QCoreApplication.translate("MainWindow", u"Username", None))
        ___qtablewidgetitem106 = self.table_users.horizontalHeaderItem(5)
        ___qtablewidgetitem106.setText(QCoreApplication.translate("MainWindow", u"Role", None))
        ___qtablewidgetitem107 = self.table_users.horizontalHeaderItem(6)
        ___qtablewidgetitem107.setText(QCoreApplication.translate("MainWindow", u"Status", None))
        ___qtablewidgetitem108 = self.table_users.horizontalHeaderItem(7)
        ___qtablewidgetitem108.setText(QCoreApplication.translate("MainWindow", u"Last Login", None))
        ___qtablewidgetitem109 = self.table_users.horizontalHeaderItem(8)
        ___qtablewidgetitem109.setText(QCoreApplication.translate("MainWindow", u"Created At", None))
        self.lbl_user_form_title.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:15px; font-weight:700; color:#FFFFFF; background:transparent;", None))
        self.lbl_user_form_title.setText(QCoreApplication.translate("MainWindow", u"User Record", None))
        self.lbl_user_id_display.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; color:#90B8E0; background:transparent;", None))
        self.lbl_user_id_display.setText(QCoreApplication.translate("MainWindow", u"#ID: \u2014", None))
        self.lbl_user_full_name.setText(QCoreApplication.translate("MainWindow", u"FULL NAME", None))
        self.lbl_user_username.setText(QCoreApplication.translate("MainWindow", u"USERNAME", None))
        self.txt_user_full_name.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Full name\u2026", None))
        self.txt_user_username.setPlaceholderText(QCoreApplication.translate("MainWindow", u"username", None))
        self.lbl_user_email.setText(QCoreApplication.translate("MainWindow", u"EMAIL", None))
        self.lbl_user_phone.setText(QCoreApplication.translate("MainWindow", u"PHONE NUMBER", None))
        self.lbl_user_phone2.setText(QCoreApplication.translate("MainWindow", u"PHONE NUMBER 2", None))
        self.txt_user_email.setPlaceholderText(QCoreApplication.translate("MainWindow", u"email@example.com", None))
        self.txt_user_phone.setPlaceholderText(QCoreApplication.translate("MainWindow", u"(000) 000-0000", None))
        self.txt_user_phone2.setPlaceholderText(QCoreApplication.translate("MainWindow", u"(000) 000-0000", None))
        self.div_user_1.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color:#EEF2F7; border-radius:0px;", None))
        self.lbl_user_password.setText(QCoreApplication.translate("MainWindow", u"PASSWORD (leave blank to keep current)", None))
        self.lbl_user_confirm_password.setText(QCoreApplication.translate("MainWindow", u"CONFIRM PASSWORD", None))
        self.txt_user_password.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022", None))
        self.txt_user_confirm_password.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022", None))
        self.div_user_2.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color:#EEF2F7; border-radius:0px;", None))
        self.lbl_user_role.setText(QCoreApplication.translate("MainWindow", u"ROLE", None))
        self.lbl_user_status.setText(QCoreApplication.translate("MainWindow", u"STATUS", None))
        self.cmb_user_role.setItemText(0, QCoreApplication.translate("MainWindow", u"ADMIN", None))
        self.cmb_user_role.setItemText(1, QCoreApplication.translate("MainWindow", u"MANAGER", None))
        self.cmb_user_role.setItemText(2, QCoreApplication.translate("MainWindow", u"EMPLOYEE", None))

        self.cmb_user_status.setItemText(0, QCoreApplication.translate("MainWindow", u"Active", None))
        self.cmb_user_status.setItemText(1, QCoreApplication.translate("MainWindow", u"Inactive", None))
        self.cmb_user_status.setItemText(2, QCoreApplication.translate("MainWindow", u"Suspended", None))

        self.div_user_3.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color:#EEF2F7; border-radius:0px;", None))
        self.lbl_user_last_login.setText(QCoreApplication.translate("MainWindow", u"LAST LOGIN", None))
        self.lbl_user_created_at.setText(QCoreApplication.translate("MainWindow", u"CREATED AT", None))
        self.txt_user_last_login.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.txt_user_created_at.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.frame_user_footer.setStyleSheet(QCoreApplication.translate("MainWindow", u"QFrame { background-color:#F8FAFD; border-top: 1px solid #EEF2F7; border-radius:0px; border-bottom-left-radius:8px; border-bottom-right-radius:8px; }", None))
        self.btn_delete_user.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.btn_save_user.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.tabWidget_user.setTabText(self.tabWidget_user.indexOf(self.tab_users_master), QCoreApplication.translate("MainWindow", u"Users", None))
        self.txt_search_products.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\U0001f50d  Search by name or type\U00002026", None))
        self.btn_refresh_products.setText(QCoreApplication.translate("MainWindow", u"\u21bb  Refresh", None))
        self.btn_export_excel_products.setText(QCoreApplication.translate("MainWindow", u"\u2913  Excel", None))
        self.btn_export_pdf_products.setText(QCoreApplication.translate("MainWindow", u"\u2913  PDF", None))
        self.btn_new_product.setText(QCoreApplication.translate("MainWindow", u"+  New Product", None))
        ___qtablewidgetitem110 = self.table_products.horizontalHeaderItem(0)
        ___qtablewidgetitem110.setText(QCoreApplication.translate("MainWindow", u"ID", None))
        ___qtablewidgetitem111 = self.table_products.horizontalHeaderItem(1)
        ___qtablewidgetitem111.setText(QCoreApplication.translate("MainWindow", u"Type", None))
        ___qtablewidgetitem112 = self.table_products.horizontalHeaderItem(2)
        ___qtablewidgetitem112.setText(QCoreApplication.translate("MainWindow", u"Name", None))
        ___qtablewidgetitem113 = self.table_products.horizontalHeaderItem(3)
        ___qtablewidgetitem113.setText(QCoreApplication.translate("MainWindow", u"Specification", None))
        ___qtablewidgetitem114 = self.table_products.horizontalHeaderItem(4)
        ___qtablewidgetitem114.setText(QCoreApplication.translate("MainWindow", u"Price", None))
        ___qtablewidgetitem115 = self.table_products.horizontalHeaderItem(5)
        ___qtablewidgetitem115.setText(QCoreApplication.translate("MainWindow", u"Brand", None))
        self.tabWidget_products_page.setTabText(self.tabWidget_products_page.indexOf(self.tab_products_list), QCoreApplication.translate("MainWindow", u"Products", None))
        self.lbl_product_form_title.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:15px; font-weight:700; color:#FFFFFF; background:transparent;", None))
        self.lbl_product_form_title.setText(QCoreApplication.translate("MainWindow", u"Product Record", None))
        self.lbl_product_id_display.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size:12px; color:#90B8E0; background:transparent;", None))
        self.lbl_product_id_display.setText(QCoreApplication.translate("MainWindow", u"#ID: \u2014", None))
        self.lbl_product_type.setText(QCoreApplication.translate("MainWindow", u"TYPE", None))
        self.txt_product_type.setPlaceholderText(QCoreApplication.translate("MainWindow", u"e.g. Flooring, Adhesive, Trim\u2026", None))
        self.lbl_product_name.setText(QCoreApplication.translate("MainWindow", u"NAME", None))
        self.lbl_product_brand.setText(QCoreApplication.translate("MainWindow", u"BRAND", None))
        self.txt_product_name.setPlaceholderText(QCoreApplication.translate("MainWindow", u"e.g. Vinyl Plank Premium", None))
        self.txt_product_brand.setPlaceholderText(QCoreApplication.translate("MainWindow", u"e.g. Mohawk, Shaw, Bostik\u2026", None))
        self.lbl_product_specification.setText(QCoreApplication.translate("MainWindow", u"SPECIFICATION", None))
        self.txt_product_specification.setPlaceholderText(QCoreApplication.translate("MainWindow", u"e.g. 6mm, Waterproof, 12x24in\u2026", None))
        self.lbl_product_price.setText(QCoreApplication.translate("MainWindow", u"PRICE", None))
        self.lbl_product_unit.setText(QCoreApplication.translate("MainWindow", u"UNIT", None))
        self.dspn_product_price.setPrefix(QCoreApplication.translate("MainWindow", u"$ ", None))
        self.txt_product_unit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"SQFT, GAL, BOX, BAG\u2026", None))
        self.lbl_product_coverage_qty.setText(QCoreApplication.translate("MainWindow", u"COVERAGE QUANTITY", None))
        self.lbl_product_coverage_unit.setText(QCoreApplication.translate("MainWindow", u"COVERAGE UNIT", None))
#if QT_CONFIG(tooltip)
        self.dspn_product_coverage_qty.setToolTip(QCoreApplication.translate("MainWindow", u"How much of the Coverage Unit is in one package (ex: 23.5 SF per box)", None))
#endif // QT_CONFIG(tooltip)
        self.txt_product_coverage_unit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"SF, LF, GAL\u2026", None))
        self.lbl_product_unit_price_display.setText(QCoreApplication.translate("MainWindow", u"\u2014", None))
        self.frame_product_footer.setStyleSheet(QCoreApplication.translate("MainWindow", u"QFrame { background-color:#F8FAFD; border-top: 1px solid #EEF2F7; border-radius:0px; border-bottom-left-radius:8px; border-bottom-right-radius:8px; }", None))
        self.btn_delete_product.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.btn_save_product.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.tabWidget_products_page.setTabText(self.tabWidget_products_page.indexOf(self.tab_product_form), QCoreApplication.translate("MainWindow", u"New / Edit Product", None))
        self.grp_settings_company.setTitle(QCoreApplication.translate("MainWindow", u"Company Information", None))
        self.lbl_settings_company_name.setText(QCoreApplication.translate("MainWindow", u"COMPANY NAME", None))
        self.lbl_settings_company_tagline.setText(QCoreApplication.translate("MainWindow", u"TAGLINE", None))
        self.lbl_settings_company_phone.setText(QCoreApplication.translate("MainWindow", u"PHONE", None))
        self.lbl_settings_company_email.setText(QCoreApplication.translate("MainWindow", u"EMAIL", None))
        self.lbl_settings_company_website.setText(QCoreApplication.translate("MainWindow", u"WEBSITE", None))
        self.grp_settings_logo.setTitle(QCoreApplication.translate("MainWindow", u"Logo", None))
        self.lbl_settings_logo_preview.setText("")
        self.btn_settings_change_logo.setText(QCoreApplication.translate("MainWindow", u"\U0001f4c1  Change Logo\U00002026", None))
        self.grp_settings_bank.setTitle(QCoreApplication.translate("MainWindow", u"Bank Information (shown on invoices)", None))
        self.lbl_settings_bank_account_no.setText(QCoreApplication.translate("MainWindow", u"ACCOUNT NUMBER", None))
        self.lbl_settings_bank_account_name.setText(QCoreApplication.translate("MainWindow", u"ACCOUNT NAME", None))
        self.lbl_settings_bank_details.setText(QCoreApplication.translate("MainWindow", u"BANK DETAILS (BANK NAME \u2014 ROUTING NUMBER)", None))
        self.grp_settings_payment_methods.setTitle(QCoreApplication.translate("MainWindow", u"Accepted Payment Methods (shown on invoices)", None))
        self.chk_settings_pm_zelle.setText(QCoreApplication.translate("MainWindow", u"Zelle", None))
        self.chk_settings_pm_check.setText(QCoreApplication.translate("MainWindow", u"Check", None))
        self.chk_settings_pm_cash.setText(QCoreApplication.translate("MainWindow", u"Cash", None))
        self.chk_settings_pm_bank_transfer.setText(QCoreApplication.translate("MainWindow", u"Bank Transfer", None))
        self.chk_settings_pm_credit_card.setText(QCoreApplication.translate("MainWindow", u"Credit Card", None))
        self.grp_settings_email.setTitle(QCoreApplication.translate("MainWindow", u"Email (for sending invoices)", None))
        self.lbl_settings_smtp_host.setText(QCoreApplication.translate("MainWindow", u"SMTP HOST", None))
        self.lbl_settings_smtp_port.setText(QCoreApplication.translate("MainWindow", u"SMTP PORT", None))
        self.txt_settings_smtp_host.setPlaceholderText(QCoreApplication.translate("MainWindow", u"smtp.gmail.com", None))
        self.lbl_settings_smtp_user.setText(QCoreApplication.translate("MainWindow", u"EMAIL ADDRESS", None))
        self.lbl_settings_smtp_password.setText(QCoreApplication.translate("MainWindow", u"APP PASSWORD", None))
        self.txt_settings_smtp_user.setPlaceholderText(QCoreApplication.translate("MainWindow", u"your-email@gmail.com", None))
        self.lbl_settings_smtp_hint.setText(QCoreApplication.translate("MainWindow", u"For Gmail, use an \"App Password\" (not your normal password) \u2014 generate one at myaccount.google.com/apppasswords", None))
        self.btn_settings_save.setText(QCoreApplication.translate("MainWindow", u"Save Settings", None))
    # retranslateUi

