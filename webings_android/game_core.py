from __future__ import annotations
import json, random, sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from kivy.utils import platform
from kivy.app import App

SKINS = ["#f8d8bf", "#e8b68e", "#c88b63", "#a76c49", "#784831", "#4e2e25"]
HAIRS = {"Preto": "#191923", "Castanho": "#65412d", "Loiro": "#dfbb70", "Ruivo": "#ae5036", "Branco": "#e2e5ec", "Azul": "#477adf"}
STYLES = ["Curto", "Médio", "Longo", "Cacheado", "Raspado"]
STAGES = [(3, "Bebê"), (6, "1ª Infância"), (10, "2ª Infância"), (13, "Pré-adolescência"), (15, "Ensino Fundamental"), (18, "Ensino Médio"), (60, "Vida Adulta"), (200, "3ª Idade")]
MAX_ACTIONS = 3
DB_FILE = Path(App.get_running_app().user_data_dir if App.get_running_app() else '.').joinpath('game_history.db')
DEFAULT_EVENTS_JSON = r'''[
 {"id":"ingles","min_age":6,"max_age":18,"title":"Um novo curso","description":"Sua família sugere que você faça um curso de inglês.","options":[{"text":"Aceitar o desafio","effects":{"inteligencia_base":8,"disposicao":-8}},{"text":"Preferir tempo livre","effects":{"felicidade":8}}]},
 {"id":"amigos","min_age":3,"max_age":80,"title":"Convite de amizade","description":"Alguém convida você para um encontro presencial.","options":[{"text":"Ir e conversar","effects":{"felicidade":12,"dependencia":-8,"disposicao":-6}},{"text":"Ficar em casa","effects":{"disposicao":7,"felicidade":-3}}]},
 {"id":"cyberbullying_01","min_age":13,"max_age":18,"title":"Comentários tóxicos na foto","description":"Uma publicação sua recebeu comentários zombando de você.","options":[{"text":"Pausar a conta e buscar apoio","requirement":{"sanidade_efetiva":20},"effects":{"dependencia":-20,"sanidade_base":10,"felicidade":-5}},{"text":"Responder a todos","requirement":{"forca_efetiva":25},"effects":{"dependencia":15,"sanidade_base":-15,"seguidores":200}},{"text":"Bloquear e denunciar","effects":{"dependencia":-10,"sanidade_base":5}}]},
 {"id":"viral","min_age":10,"max_age":80,"title":"Vídeo viral","description":"Um vídeo seu começa a alcançar muita gente.","options":[{"text":"Publicar ainda mais","effects":{"seguidores":350,"dependencia":15,"disposicao":-12}},{"text":"Aproveitar com moderação","effects":{"seguidores":120,"felicidade":8,"dependencia":3}},{"text":"Desligar notificações","effects":{"dependencia":-12,"sanidade_base":6}}]},
 {"id":"comparacao","min_age":10,"max_age":80,"title":"Comparação nas redes","description":"Ao ver perfis idealizados, você começa a comparar sua vida.","options":[{"text":"Continuar rolando","effects":{"dependencia":15,"felicidade":-12}},{"text":"Fazer uma pausa consciente","effects":{"dependencia":-12,"sanidade_base":8,"felicidade":5}}]},
 {"id":"esporte","min_age":6,"max_age":80,"title":"Dia ao ar livre","description":"Surge a chance de participar de uma atividade física em grupo.","options":[{"text":"Participar","effects":{"hp":8,"forca_base":7,"disposicao":-10}},{"text":"Descansar","effects":{"disposicao":10}}]},
 {"id":"noticias","min_age":13,"max_age":80,"title":"Notícias em excesso","description":"Seu feed está cheio de notícias preocupantes.","options":[{"text":"Ler sem parar","effects":{"dependencia":12,"felicidade":-10}},{"text":"Selecionar fontes e fazer pausas","effects":{"dependencia":-8,"foco_base":5}}]},
 {"id":"projeto","min_age":10,"max_age":80,"title":"Projeto criativo","description":"Você pode aprender uma habilidade e publicar o resultado.","options":[{"text":"Criar com calma","effects":{"inteligencia_base":8,"seguidores":40,"disposicao":-8}},{"text":"Buscar apenas curtidas","effects":{"seguidores":150,"dependencia":12}}]},
 {"id":"familia","min_age":1,"max_age":80,"title":"Tempo em família","description":"Você tem uma oportunidade de passar tempo com pessoas próximas.","options":[{"text":"Aproveitar a companhia","effects":{"felicidade":12,"sanidade_base":5,"dependencia":-5}},{"text":"Preferir as telas","effects":{"felicidade":5,"dependencia":10}}]},
 {"id":"sono","min_age":1,"max_age":80,"title":"Uma semana cansativa","description":"Sua rotina ficou mais intensa do que o esperado.","options":[{"text":"Priorizar descanso","effects":{"disposicao":15,"dependencia":-5}},{"text":"Procurar distração online","effects":{"felicidade":8,"dependencia":12,"disposicao":-10}}]},
 {"id":"trabalho","min_age":18,"max_age":80,"title":"Pressão profissional","description":"Uma tarefa importante exige sua atenção.","options":[{"text":"Planejar e executar","effects":{"foco_base":7,"disposicao":-12}},{"text":"Adiar olhando o celular","effects":{"dependencia":12,"felicidade":-8}}]}
]'''
@dataclass
class Player:
    nome: str
    sobrenome: str
    genero: str
    pele: str
    cabelo: str
    estilo: str
    origem: str
    idade: int = 1
    hp: int = 75
    disposicao: int = 75
    felicidade: int = 75
    dependencia: int = 15
    foco_base: int = 25
    sanidade_base: int = 25
    forca_base: int = 15
    inteligencia_base: int = 30
    seguidores: int = 0
    historico_eventos: list[str] = field(default_factory=list)
    fases_vividas: list[str] = field(default_factory=list)
    desafios_feitos: list[int] = field(default_factory=list)
    acoes_ano: int = 0
    causa_morte: Optional[str] = None
    registrado: bool = False

    def __post_init__(self) -> None:
        bonus = {"Nerd de TI": ("inteligencia_base", 15), "Atleta da Turma": ("forca_base", 15), "Extrovertido": ("sanidade_base", 15)}
        if self.origem in bonus:
            attr, val = bonus[self.origem]
            setattr(self, attr, getattr(self, attr) + val)
        elif self.origem == "Criador de Conteúdo":
            self.seguidores = 200
            self.dependencia += 15
        self.fases_vividas.append(self.fase)

    @property
    def nome_completo(self) -> str:
        return f"{self.nome} {self.sobrenome}"

    @property
    def fase(self) -> str:
        if self.causa_morte:
            return "Morte"
        return next((name for max_age, name in STAGES if self.idade < max_age), "3ª Idade")

    @property
    def foco_efetivo(self) -> int:
        return max(0, self.foco_base + self.disposicao // 2 - self.dependencia // 2)

    @property
    def sanidade_efetiva(self) -> int:
        return max(0, self.sanidade_base + self.felicidade // 2 - self.dependencia // 2)

    @property
    def forca_efetiva(self) -> int:
        return max(0, self.forca_base + self.hp // 2 + self.disposicao // 2)

    @property
    def inteligencia_efetiva(self) -> int:
        return max(0, self.inteligencia_base - self.dependencia // 2)

    @property
    def badge(self) -> str:
        if self.dependencia < 20 and self.sanidade_efetiva > 70:
            return "🏆 O Desconectado"
        if self.dependencia > 80 and self.seguidores > 1000:
            return "📱 Escravo do Algoritmo"
        if self.idade >= 60 and self.hp > 60 and self.sanidade_efetiva > 60:
            return "⚖ Mestre do Equilíbrio"
        return "🌱 Uma Vida de Aprendizados"

    def effect(self, changes: dict[str, int]) -> None:
        allowed = {"hp", "disposicao", "felicidade", "dependencia", "foco_base", "sanidade_base", "forca_base", "inteligencia_base", "seguidores"}
        for key, value in changes.items():
            if key not in allowed or not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"Efeito inválido: {key}")
            old = getattr(self, key)
            new = old + value
            if key == "seguidores":
                new = max(0, new)
            else:
                new = max(0, min(100, new))
            setattr(self, key, new)
        self.check_death()

    def check_death(self) -> None:
        if self.causa_morte:
            return
        if self.hp <= 0:
            self.causa_morte = "Morte física — Vira Esqueletinho"
        elif self.felicidade <= 0:
            self.causa_morte = "Colapso emocional / Burnout severo"

    def log(self, message: str) -> None:
        self.historico_eventos.append(f"[Idade {self.idade}] {message}")


ACTIVITIES: dict[str, dict[str, Any]] = {
    "Exercício Físico": {"requirements": {"forca_efetiva": 20, "foco_efetivo": 10}, "effects": {"forca_base": 15, "hp": 10, "disposicao": -20}},
    "Estudar": {"requirements": {"inteligencia_efetiva": 20, "foco_efetivo": 15}, "effects": {"inteligencia_base": 15, "disposicao": -15}},
    "Socializar": {"requirements": {"sanidade_efetiva": 25}, "effects": {"felicidade": 20, "sanidade_base": 10, "dependencia": -15, "disposicao": -10}},
    "Criar Conteúdo": {"requirements": {"idade": 10, "foco_efetivo": 25}, "effects": {"dependencia": 10, "felicidade": 15, "disposicao": -20}},
    "Doomscrolling": {"requirements": {}, "effects": {"felicidade": 10, "disposicao": -15, "dependencia": 15}},
    "Detox Digital": {"requirements": {"sanidade_efetiva": 15}, "effects": {"dependencia": -25, "sanidade_base": 15, "disposicao": -10}},
}

GATES = {
    12: ("Prova Escolar", {"inteligencia_efetiva": 30, "foco_efetivo": 20}, {"felicidade": -30, "hp": -15}),
    15: ("Campeonato Esportivo", {"forca_efetiva": 35, "foco_efetivo": 25}, {"felicidade": -30, "hp": -20}),
    18: ("Entrevista de Emprego", {"sanidade_efetiva": 35, "inteligencia_efetiva": 35}, {"felicidade": -40, "dependencia": 20}),
}

ROUTINES = {
    "Dormir Cedo": {"disposicao": 30, "hp": 10, "dependencia": -5},
    "Redes na Cama": {"felicidade": 15, "disposicao": -20, "dependencia": 15},
    "Ler um Livro": {"inteligencia_base": 10, "disposicao": 15, "dependencia": -5},
}


def requirements_met(player: Player, requirements: dict[str, int]) -> bool:
    return all(getattr(player, attr, -1) >= minimum for attr, minimum in requirements.items())


class GameEngine:
    def __init__(self, player: Player) -> None:
        self.player = player
        self.events = self._load_events()

    @staticmethod
    def _load_events() -> list[dict[str, Any]]:
        source = Path(__file__).resolve().with_name("events.json")
        try:
            raw = source.read_text(encoding="utf-8") if source.is_file() else DEFAULT_EVENTS_JSON
            data = json.loads(raw)
            if not isinstance(data, list) or not data:
                raise ValueError("JSON de eventos vazio")
            for item in data:
                if not isinstance(item, dict) or not all(k in item for k in ("min_age", "max_age", "title", "description", "options")):
                    raise ValueError("Evento malformado")
                if not isinstance(item["options"], list) or not item["options"]:
                    raise ValueError("Evento sem opções")
            return data
        except (OSError, ValueError, TypeError, KeyError) as exc:
            print(f"Aviso: eventos externos inválidos ({exc}); usando eventos internos.")
            return json.loads(DEFAULT_EVENTS_JSON)

    def activity(self, name: str) -> None:
        p = self.player
        if p.causa_morte:
            raise ValueError("Esta vida já terminou.")
        if p.acoes_ano >= MAX_ACTIONS:
            raise ValueError("Você já fez 3 atividades neste ano. Hora de dormir!")
        if name not in ACTIVITIES:
            raise ValueError("Atividade desconhecida")
        spec = ACTIVITIES[name]
        if not requirements_met(p, spec["requirements"]):
            raise ValueError("Seus atributos ainda não atendem aos requisitos.")
        effects = dict(spec["effects"])
        if name == "Criar Conteúdo":
            effects["seguidores"] = p.inteligencia_base * 3
        p.effect(effects)
        p.acoes_ano += 1
        p.log(f"Atividade: {name}. {format_effects(effects)}")

    def gate(self) -> Optional[tuple[str, bool, dict[str, int]]]:
        p = self.player
        if p.idade not in GATES or p.idade in p.desafios_feitos:
            return None
        title, req, penalty = GATES[p.idade]
        passed = requirements_met(p, req)
        p.desafios_feitos.append(p.idade)
        if not passed:
            p.effect(penalty)
        p.log(f"Desafio obrigatório — {title}: {'aprovado!' if passed else 'não superado.'}")
        return title, passed, penalty

    def sleep(self, routine: str) -> Optional[dict[str, Any]]:
        p = self.player
        if p.causa_morte:
            return None
        if routine not in ROUTINES:
            raise ValueError("Rotina inválida")
        p.effect(ROUTINES[routine])
        p.log(f"Rotina noturna: {routine}. {format_effects(ROUTINES[routine])}")
        if p.causa_morte:
            return None
        p.idade += 1
        p.acoes_ano = 0
        if p.fase not in p.fases_vividas:
            p.fases_vividas.append(p.fase)
            p.log(f"Nova fase da vida: {p.fase}.")
        if p.dependencia > 50:
            p.effect({"disposicao": -5, "felicidade": -3})
            p.log("Dependência digital elevada: -5 disposição, -3 felicidade.")
        if p.disposicao == 0:
            p.effect({"hp": -15})
            p.log("Exaustão: -15 de saúde.")
        if p.idade >= 80 and not p.causa_morte:
            chance = min(0.95, 0.08 + (p.idade - 80) * 0.045)
            if random.random() < chance:
                p.causa_morte = "Causas naturais — fim da vida"
        if p.causa_morte:
            return None
        eligible = [e for e in self.events if e["min_age"] <= p.idade <= e["max_age"]]
        return random.choice(eligible) if eligible else None

    def choose_event(self, event: dict[str, Any], option: dict[str, Any]) -> None:
        if option not in event["options"]:
            raise ValueError("Escolha inválida")
        if not requirements_met(self.player, option.get("requirement", {})):
            raise ValueError("Requisitos insuficientes para essa escolha")
        self.player.effect(option.get("effects", {}))
        self.player.log(f"{event['title']}: {option['text']}. {format_effects(option.get('effects', {}))}")


def format_effects(effects: dict[str, int]) -> str:
    labels = {"hp": "Saúde", "disposicao": "Disposição", "felicidade": "Felicidade", "dependencia": "Dependência", "sanidade_base": "Sanidade", "foco_base": "Foco", "forca_base": "Força", "inteligencia_base": "Inteligência", "seguidores": "Seguidores"}
    return " · ".join(f"{labels.get(k, k)} {v:+d}" for k, v in effects.items())


class PersistenceManager:
    def __init__(self, path: Path = DB_FILE) -> None:
        self.path = path
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS partidas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL, sobrenome TEXT NOT NULL, genero TEXT NOT NULL,
                pele TEXT NOT NULL, cabelo TEXT NOT NULL, estilo TEXT NOT NULL,
                origem TEXT NOT NULL, idade_final INTEGER NOT NULL,
                seguidores INTEGER NOT NULL, causa_morte TEXT NOT NULL,
                badge TEXT NOT NULL, fases_json TEXT NOT NULL,
                historico_json TEXT NOT NULL, criada_em TEXT NOT NULL
            )""")

    def save(self, p: Player) -> None:
        if p.registrado or not p.causa_morte:
            return
        with sqlite3.connect(self.path) as db:
            db.execute("""INSERT INTO partidas
                (nome,sobrenome,genero,pele,cabelo,estilo,origem,idade_final,seguidores,
                causa_morte,badge,fases_json,historico_json,criada_em)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                p.nome, p.sobrenome, p.genero, p.pele, p.cabelo, p.estilo, p.origem,
                p.idade, p.seguidores, p.causa_morte, p.badge,
                json.dumps(p.fases_vividas, ensure_ascii=False),
                json.dumps(p.historico_eventos, ensure_ascii=False),
                datetime.now().isoformat(timespec="seconds")))
        p.registrado = True


