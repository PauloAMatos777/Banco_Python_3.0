import textwrap
from abc import ABC, abstractmethod
from datetime import datetime


class IteradorDeContas:
    def __init__(self, contas):
        self.contas = contas
        self._indice = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._indice >= len(self.contas):
            raise StopIteration
        conta = self.contas[self._indice]
        self._indice += 1
        return f"""\
        Agência:\t{conta.agencia}
        Número:\t\t{conta.numero}
        Titular:\t{conta.cliente.nome}
        Saldo:\t\tR$ {conta.saldo:.2f}
        """


class Cliente:
    def __init__(self, endereco):
        self.endereco = endereco
        self.contas = []

    def realizar_transacao(self, conta, transacao):
        transacao.executar(conta)

    def adicionar_conta(self, conta):
        self.contas.append(conta)


class PessoaFisica(Cliente):
    def __init__(self, nome, data_nascimento, cpf, endereco):
        super().__init__(endereco)
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf


class Conta:
    def __init__(self, numero, cliente):
        self._saldo = 0
        self._numero = numero
        self._agencia = "0001"
        self._cliente = cliente
        self._historico = Historico()

    @classmethod
    def criar_nova_conta(cls, cliente, numero):
        return cls(numero, cliente)

    @property
    def saldo(self):
        return self._saldo

    @property
    def numero(self):
        return self._numero

    @property
    def agencia(self):
        return self._agencia

    @property
    def cliente(self):
        return self._cliente

    @property
    def historico(self):
        return self._historico

    def sacar(self, valor):
        if valor <= 0:
            print("\nXXX Valor inválido para saque! XXX")
            return False
        if valor > self._saldo:
            print("\nXXX Saldo insuficiente! XXX")
            return False
        self._saldo -= valor
        print("\n$$$ Saque realizado com sucesso! $$$")
        return True

    def depositar(self, valor):
        if valor <= 0:
            print("\nXXX Valor inválido para depósito! XXX")
            return False
        self._saldo += valor
        print("\n$$$ Depósito realizado com sucesso! $$$")
        return True


class ContaCorrente(Conta):
    def __init__(self, numero, cliente, limite=500, limite_saques=3):
        super().__init__(numero, cliente)
        self._limite = limite
        self._limite_saques = limite_saques

    @classmethod
    def criar_nova_conta(cls, cliente, numero, limite, limite_saques):
        return cls(numero, cliente, limite, limite_saques)

    def sacar(self, valor):
        saques_realizados = len(
            [transacao for transacao in self.historico.transacoes if isinstance(transacao, Saque)]
        )

        if valor > self._limite:
            print("\nXXX Saque excede o limite permitido! XXX")
            return False

        if saques_realizados >= self._limite_saques:
            print("\nXXX Limite de saques diários excedido! XXX")
            return False

        return super().sacar(valor)

    def __str__(self):
        return f"""\
        Agência:\t{self.agencia}
        Conta Corrente:\t{self.numero}
        Titular:\t{self.cliente.nome}
        """


class Historico:
    def __init__(self):
        self._transacoes = []

    @property
    def transacoes(self):
        return self._transacoes

    def registrar_transacao(self, transacao):
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            }
        )

    def gerar_relatorio(self, tipo_transacao=None):
        for transacao in self._transacoes:
            if tipo_transacao is None or transacao["tipo"].lower() == tipo_transacao.lower():
                yield transacao


class Transacao(ABC):
    @property
    @abstractmethod
    def valor(self):
        pass

    @abstractmethod
    def executar(self, conta):
        pass


class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def executar(self, conta):
        if conta.sacar(self._valor):
            conta.historico.registrar_transacao(self)


class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def executar(self, conta):
        if conta.depositar(self._valor):
            conta.historico.registrar_transacao(self)


def log_transacao(func):
    def decorador(*args, **kwargs):
        resultado = func(*args, **kwargs)
        print(f"{datetime.now()}: Transação {func.__name__.upper()} executada")
        return resultado

    return decorador


def menu():
    return input(textwrap.dedent("""\n
    ================ MENU ================
    [d] Depositar
    [s] Sacar
    [e] Extrato
    [nc] Nova conta
    [lc] Listar contas
    [nu] Novo usuário
    [q] Sair
    => """))


def buscar_cliente_por_cpf(cpf, clientes):
    return next((cliente for cliente in clientes if cliente.cpf == cpf), None)


def obter_conta_cliente(cliente):
    if not cliente.contas:
        print("\n@@@ Cliente não possui conta! @@@")
        return None
    return cliente.contas[0]


@log_transacao
def realizar_deposito(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = buscar_cliente_por_cpf(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor do depósito: "))
    conta = obter_conta_cliente(cliente)

    if conta:
        transacao = Deposito(valor)
        cliente.realizar_transacao(conta, transacao)


@log_transacao
def realizar_saque(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = buscar_cliente_por_cpf(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor do saque: "))
    conta = obter_conta_cliente(cliente)

    if conta:
        transacao = Saque(valor)
        cliente.realizar_transacao(conta, transacao)


@log_transacao
def exibir_extrato(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = buscar_cliente_por_cpf(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    conta = obter_conta_cliente(cliente)
    if not conta:
        return

    print("\n================ EXTRATO ================")
    for transacao in conta.historico.gerar_relatorio():
        print(f"{transacao['tipo']}:\n\tR$ {transacao['valor']:.2f}")
    print(f"\nSaldo atual: R$ {conta.saldo:.2f}")
    print("==========================================")


@log_transacao
def criar_novo_cliente(clientes):
    cpf = input("Informe o CPF: ")
    if buscar_cliente_por_cpf(cpf, clientes):
        print("\n@@@ CPF já cadastrado! @@@")
        return

    nome = input("Informe o nome completo: ")
    data_nascimento = input("Informe a data de nascimento (dd-mm-aaaa): ")
    endereco = input("Informe o endereço: ")
    
    novo_cliente = PessoaFisica(nome, data_nascimento, cpf, endereco)
    clientes.append(novo_cliente)
    print("\n=== Cliente criado com sucesso! ===")


@log_transacao
def criar_nova_conta(numero_conta, clientes, contas):
    cpf = input("Informe o CPF do cliente: ")
    cliente = buscar_cliente_por_cpf(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    nova_conta = ContaCorrente.criar_nova_conta(cliente, numero_conta, limite=500, limite_saques=5)
    contas.append(nova_conta)
    cliente.adicionar_conta(nova_conta)
    print("\n=== Conta criada com sucesso! ===")


def listar_todas_contas(contas):
    for conta in IteradorDeContas(contas):
        print("=" * 100)
        print(conta)


def main():
    clientes = []
    contas = []

    while True:
        opcao = menu()

        if opcao == "d":
            realizar_deposito(clientes)
        elif opcao == "s":
            realizar_saque(clientes)
        elif opcao == "e":
            exibir_extrato(clientes)
        elif opcao == "nc":
            criar_nova_conta(len(contas) + 1, clientes, contas)
        elif opcao == "nu":
            criar_novo_cliente(clientes)
        elif opcao == "lc":
            listar_todas_contas(contas)
        elif opcao == "q":
            break
        else:
            print("\n@@@ Opção inválida! @@@")

if __name__ == "__main__":
    main()
