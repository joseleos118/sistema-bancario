
class BancoError(Exception):
    """Excepción base del sistema bancario."""

    def __init__(self, mensaje, codigo):
        super().__init__(mensaje)
        self.codigo = codigo


class SaldoInsuficienteError(BancoError):
    """Se lanza cuando el saldo no alcanza para realizar un retiro."""

    def __init__(self, saldo_actual, monto_solicitado):
        self.saldo_actual = saldo_actual
        self.monto_solicitado = monto_solicitado
        self.deficit = monto_solicitado - saldo_actual

        mensaje = (
            f"Saldo insuficiente: tienes ${saldo_actual:.2f}, "
            f"necesitas ${monto_solicitado:.2f} "
            f"(faltan ${self.deficit:.2f})"
        )

        super().__init__(mensaje, "SALDO_INSUFICIENTE")


class CuentaNoEncontradaError(BancoError):
    """Se lanza cuando una cuenta no existe."""

    def __init__(self, numero_cuenta):
        self.numero_cuenta = numero_cuenta
        super().__init__(
            f"La cuenta {numero_cuenta} no existe",
            "CUENTA_NO_ENCONTRADA"
        )


class CuentaBloqueadaError(BancoError):
    """Se lanza cuando se intenta operar con una cuenta bloqueada."""

    def __init__(self, numero_cuenta):
        self.numero_cuenta = numero_cuenta
        super().__init__(
            f"La cuenta {numero_cuenta} está bloqueada",
            "CUENTA_BLOQUEADA"
        )


class MontoInvalidoError(BancoError):
    """Se lanza cuando el monto no es positivo."""

    def __init__(self, monto):
        self.monto = monto
        super().__init__(
            f"Monto inválido: {monto}. Debe ser positivo",
            "MONTO_INVALIDO"
        )


class LimiteDiarioExcedidoError(BancoError):
    """Se lanza cuando se supera el límite diario de retiros."""

    def __init__(self, limite, retirado_hoy, monto_solicitado):
        self.limite = limite
        self.retirado_hoy = retirado_hoy
        self.monto_solicitado = monto_solicitado

        mensaje = (
            f"Límite diario excedido: límite ${limite:.2f}, "
            f"retirado hoy ${retirado_hoy:.2f}, "
            f"solicitado ${monto_solicitado:.2f}"
        )

        super().__init__(mensaje, "LIMITE_EXCEDIDO")


class CuentaBancaria:
    """Representa una cuenta bancaria."""

    LIMITE_DIARIO = 10000

    def __init__(self, numero, titular, saldo_inicial):
        self.numero = numero
        self.titular = titular
        self._saldo = 0
        self._bloqueada = False
        self._retirado_hoy = 0
        self._historial = []

        if saldo_inicial < 0:
            raise MontoInvalidoError(saldo_inicial)

        if saldo_inicial > 0:
            self.depositar(saldo_inicial)

    @property
    def saldo(self):
        """Permite consultar el saldo sin modificarlo."""
        return self._saldo

    def depositar(self, monto):
        """Deposita dinero en la cuenta."""
        if self._bloqueada:
            raise CuentaBloqueadaError(self.numero)

        if monto <= 0:
            raise MontoInvalidoError(monto)

        self._saldo += monto
        self._historial.append(f"Depósito: ${monto:.2f}")
        print(f"Depósito realizado. Saldo actual: ${self._saldo:.2f}")

    def retirar(self, monto):
        """Retira dinero validando saldo y límite diario."""
        if self._bloqueada:
            raise CuentaBloqueadaError(self.numero)

        if monto <= 0:
            raise MontoInvalidoError(monto)

        if self._saldo < monto:
            raise SaldoInsuficienteError(self._saldo, monto)

        if self._retirado_hoy + monto > self.LIMITE_DIARIO:
            raise LimiteDiarioExcedidoError(
                self.LIMITE_DIARIO,
                self._retirado_hoy,
                monto
            )

        self._saldo -= monto
        self._retirado_hoy += monto
        self._historial.append(f"Retiro: ${monto:.2f}")
        print(f"Retiro realizado. Saldo actual: ${self._saldo:.2f}")

    def consultar_saldo(self):
        """Muestra el saldo disponible."""
        if self._bloqueada:
            raise CuentaBloqueadaError(self.numero)

        print(f"Saldo de {self.titular}: ${self._saldo:.2f}")

    def bloquear(self):
        """Bloquea la cuenta."""
        self._bloqueada = True
        self._historial.append("Cuenta bloqueada")
        print("Cuenta bloqueada correctamente.")

    def desbloquear(self):
        """Desbloquea la cuenta."""
        self._bloqueada = False
        self._historial.append("Cuenta desbloqueada")
        print("Cuenta desbloqueada correctamente.")

    def mostrar_historial(self):
        """Muestra las transacciones de la cuenta."""
        if not self._historial:
            print("No hay transacciones registradas.")
        else:
            print(f"\nHistorial de {self.titular}:")
            for movimiento in self._historial:
                print(movimiento)


class Banco:
    """Administra las cuentas bancarias."""

    _cuentas = {}

    def crear_cuenta(self, numero, titular, saldo_inicial):
        """Crea una cuenta con un número único."""
        if numero in self._cuentas:
            raise BancoError(
                f"El número de cuenta {numero} ya existe",
                "CUENTA_DUPLICADA"
            )

        cuenta = CuentaBancaria(numero, titular, saldo_inicial)
        self._cuentas[numero] = cuenta
        print(f"Cuenta creada correctamente para {titular}.")

    def obtener_cuenta(self, numero):
        """Busca una cuenta por su número."""
        try:
            return self._cuentas[numero]
        except KeyError as error:
            raise CuentaNoEncontradaError(numero) from error

    def transferir(self, origen, destino, monto):
        """Transfiere dinero entre dos cuentas."""
        cuenta_origen = self.obtener_cuenta(origen)
        cuenta_destino = self.obtener_cuenta(destino)

        try:
            cuenta_origen.retirar(monto)
            cuenta_destino.depositar(monto)

        except BancoError:
            print("La transferencia no pudo completarse.")
            raise

        else:
            cuenta_origen._historial.append(
                f"Transferencia enviada a {destino}: ${monto:.2f}"
            )
            cuenta_destino._historial.append(
                f"Transferencia recibida de {origen}: ${monto:.2f}"
            )
            print("Transferencia realizada correctamente.")

        finally:
            print("Proceso de transferencia finalizado.")

    @classmethod
    def total_cuentas(cls):
        """Devuelve el total de cuentas registradas."""
        return len(cls._cuentas)


def registrar_error(error):
    """Registra los errores del sistema bancario."""
    print(f"[ERROR {error.codigo}] {error}")


def obtener_monto(mensaje):
    """Solicita un monto numérico al usuario."""
    while True:
        try:
            monto = float(input(mensaje))
            return monto
        except ValueError as error:
            print("Error: ingresa una cantidad numérica válida.")
            print(f"Detalle: {error}")


def main():
    banco = Banco()

    while True:
        print("\n========================================")
        print("          SISTEMA BANCARIO")
        print("========================================")
        print("1. Crear cuenta")
        print("2. Depositar")
        print("3. Retirar")
        print("4. Transferir")
        print("5. Consultar saldo")
        print("6. Bloquear/desbloquear cuenta")
        print("7. Ver historial")
        print("8. Salir")
        print("========================================")

        opcion = input("Seleccione una opción: ")

        try:
            if opcion == "1":
                numero = input("Número de cuenta: ")
                titular = input("Nombre del titular: ")
                saldo = obtener_monto("Saldo inicial: ")

                banco.crear_cuenta(numero, titular, saldo)

            elif opcion == "2":
                numero = input("Número de cuenta: ")
                cuenta = banco.obtener_cuenta(numero)
                monto = obtener_monto("Monto a depositar: ")
                cuenta.depositar(monto)

            elif opcion == "3":
                numero = input("Número de cuenta: ")
                cuenta = banco.obtener_cuenta(numero)
                monto = obtener_monto("Monto a retirar: ")
                cuenta.retirar(monto)

            elif opcion == "4":
                origen = input("Cuenta de origen: ")
                destino = input("Cuenta de destino: ")
                monto = obtener_monto("Monto a transferir: ")
                banco.transferir(origen, destino, monto)

            elif opcion == "5":
                numero = input("Número de cuenta: ")
                cuenta = banco.obtener_cuenta(numero)
                cuenta.consultar_saldo()

            elif opcion == "6":
                numero = input("Número de cuenta: ")
                cuenta = banco.obtener_cuenta(numero)

                if cuenta._bloqueada:
                    cuenta.desbloquear()
                else:
                    cuenta.bloquear()

            elif opcion == "7":
                numero = input("Número de cuenta: ")
                cuenta = banco.obtener_cuenta(numero)
                cuenta.mostrar_historial()

            elif opcion == "8":
                print("Gracias por utilizar el sistema bancario.")
                break

            else:
                print("Opción no válida.")

        except SaldoInsuficienteError as error:
            registrar_error(error)

        except CuentaNoEncontradaError as error:
            registrar_error(error)

        except CuentaBloqueadaError as error:
            registrar_error(error)

        except MontoInvalidoError as error:
            registrar_error(error)

        except LimiteDiarioExcedidoError as error:
            registrar_error(error)

        except BancoError as error:
            registrar_error(error)

        except KeyboardInterrupt:
            print("\nOperación interrumpida por el usuario.")

        finally:
            print("Fin de la operación.")


if __name__ == "__main__":
    main()
