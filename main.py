import json
import networkx as nx
import matplotlib.pyplot as plt


def carregar_json(caminho_arquivo):
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        return json.load(f)


def construir_mapa_de_nomes(usuarios, grupos, computadores):
    """
    Cria um dicionário SID -> nome legível, consultando os 3 arquivos.
    Isso resolve o problema de tudo vir como SID nos dados reais.
    """
    mapa = {}

    for u in usuarios["data"]:
        mapa[u["ObjectIdentifier"]] = ("User", u["Properties"]["name"])

    for g in grupos["data"]:
        mapa[g["ObjectIdentifier"]] = ("Group", g["Properties"]["name"])

    for c in computadores["data"]:
        mapa[c["ObjectIdentifier"]] = ("Computer", c["Properties"]["name"])

    return mapa


def rotulo(sid, mapa):
    """Transforma um SID no rótulo 'Tipo: Nome' usado como nó do grafo"""
    tipo, nome = mapa.get(sid, ("Unknown", sid))
    return f"{tipo}: {nome}"


def construir_grafo(usuarios, grupos, computadores, mapa):
    grafo = nx.DiGraph()

    # Relação MemberOf: cada membro de um grupo aponta para o grupo
    for g in grupos["data"]:
        no_grupo = rotulo(g["ObjectIdentifier"], mapa)
        for membro in g.get("Members", []):
            no_membro = rotulo(membro["ObjectIdentifier"], mapa)
            grafo.add_edge(no_membro, no_grupo, relation="MemberOf")

    # Relações ligadas a computadores: AdminTo e HasSession
    for c in computadores["data"]:
        no_pc = rotulo(c["ObjectIdentifier"], mapa)

        admins = c.get("LocalAdmins", {}).get("Results", [])
        for admin in admins:
            no_admin = rotulo(admin["ObjectIdentifier"], mapa)
            grafo.add_edge(no_admin, no_pc, relation="AdminTo")

        sessoes = c.get("Sessions", {}).get("Results", [])
        for sessao in sessoes:
            no_usuario = rotulo(sessao["ObjectIdentifier"], mapa)
            grafo.add_edge(no_pc, no_usuario, relation="HasSession")

    return grafo


def listar_usuarios(grafo):
    return [n for n in grafo.nodes() if n.startswith("User: ")]


def listar_grupos_sensiveis(grafo, nomes_sensiveis):
    todos_grupos = [n for n in grafo.nodes() if n.startswith("Group: ")]
    # Compara ignorando "@CORP.LOCAL" e maiúsculas/minúsculas
    resultado = []
    for g in todos_grupos:
        nome_limpo = g.replace("Group: ", "").split("@")[0].strip().upper()
        if nome_limpo in [n.upper() for n in nomes_sensiveis]:
            resultado.append(g)
    return resultado


def mapear_todos_caminhos_criticos(grafo, grupos_sensiveis):
    usuarios = listar_usuarios(grafo)
    resultados = []

    for usuario in usuarios:
        for grupo in grupos_sensiveis:
            if nx.has_path(grafo, usuario, grupo):
                caminho = nx.shortest_path(grafo, source=usuario, target=grupo)
                if len(caminho) > 2:
                    resultados.append(caminho)

    return resultados


def desenhar_grafo(grafo, caminhos_destacados=None):
    pos = nx.spring_layout(grafo, seed=42)

    arestas_criticas = set()
    if caminhos_destacados:
        for caminho in caminhos_destacados:
            for i in range(len(caminho) - 1):
                arestas_criticas.add((caminho[i], caminho[i + 1]))

    cores_arestas = [
        "red" if (u, v) in arestas_criticas else "gray"
        for u, v in grafo.edges()
    ]

    nx.draw(
        grafo, pos, with_labels=True,
        node_color="lightblue", node_size=2000,
        font_size=7, edge_color=cores_arestas, width=2, arrows=True
    )
    plt.title("Caminhos de elevação de privilégio no AD")
    plt.show()


if __name__ == "__main__":
    usuarios = carregar_json("corp_users.json")
    grupos = carregar_json("corp_groups.json")
    computadores = carregar_json("corp_computers.json")

    mapa_nomes = construir_mapa_de_nomes(usuarios, grupos, computadores)
    grafo = construir_grafo(usuarios, grupos, computadores, mapa_nomes)

    GRUPOS_CRITICOS = ["DOMAIN ADMINS", "ENTERPRISE ADMINS", "ADMINISTRATORS"]
    grupos_alvo = listar_grupos_sensiveis(grafo, GRUPOS_CRITICOS)

    caminhos_encontrados = []
    if not grupos_alvo:
        print("Nenhum grupo crítico configurado foi encontrado no grafo.")
    else:
        caminhos_encontrados = mapear_todos_caminhos_criticos(grafo, grupos_alvo)
        if caminhos_encontrados:
            print(f"⚠️  {len(caminhos_encontrados)} caminho(s) de elevação de privilégio encontrado(s):\n")
            for caminho in caminhos_encontrados:
                print(" -> ".join(caminho))
                print()
        else:
            print("Nenhum caminho de elevação de privilégio encontrado.")

    desenhar_grafo(grafo, caminhos_destacados=caminhos_encontrados)