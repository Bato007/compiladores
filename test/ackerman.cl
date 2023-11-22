class Ackerman {
	ackerman(m: Int, n: Int) : Int {
		if m = 0 then
			n + 1
		else if n = 0 then
			ackerman(m - 1, 1)
		else
			ackerman(m - 1, ackerman(m, n - 1))
		fi fi
	};
};
class Main inherits IO {
	acka : Ackerman; 
	result: Int;
    main() : SELF_TYPE {
	{
		acka <- (new Ackerman);
		result <- acka.ackerman(3, 4);
		out_string("El resultado de m-3 y n=4 de ackerman es: ");
		out_int(result);
	    out_string("\n");
	}
    };
};