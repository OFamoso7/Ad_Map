AD Attack Path Mapper: uma ferramenta em Python que modela um ambiente de Active Directory como um grafo direcionado e identifica caminhos de elevacao de privilegio ate grupos criticos (Domain Admins, Enterprise Admins), no estilo do BloodHound.

O que a ferramenta faz:
- Ingestao de dados offline (formato compativel com exports do SharpHound)
- Resolucao de SIDs para nomes legiveis
- Construcao de grafo com NetworkX (nos = usuarios/grupos/computadores, arestas = relacoes como MemberOf, AdminTo, HasSession)
- Varredura automatica de todos os usuarios contra todos os grupos sensiveis, sem hardcode de nomes
- Visualizacao destacando as rotas criticas
