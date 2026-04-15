require("dotenv").config();
const express = require("express");
const jwt = require("jsonwebtoken");
const bcrypt = require("bcryptjs");
const { Pool } = require("pg");

const app = express();
app.use(express.json());

const pool = new Pool({
  host: process.env.DB_HOST,
  port: Number(process.env.DB_PORT) || 5432,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
});

const JWT_SECRET = process.env.JWT_SECRET || "dev-secret";
const PORT = process.env.PORT || 3001;

// POST /auth/login
app.post("/auth/login", async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password)
    return res.status(400).json({ error: "email e password são obrigatórios" });

  const { rows } = await pool.query("SELECT * FROM users WHERE email = $1", [email]);
  const user = rows[0];
  if (!user || !(await bcrypt.compare(password, user.password_hash)))
    return res.status(401).json({ error: "Credenciais inválidas" });

  const token = jwt.sign({ sub: user.id, email: user.email }, JWT_SECRET, {
    expiresIn: "15m",
  });
  const refresh = jwt.sign({ sub: user.id }, JWT_SECRET, { expiresIn: "7d" });

  res.json({ token, refresh });
});

// POST /auth/refresh
app.post("/auth/refresh", (req, res) => {
  const { refresh } = req.body;
  if (!refresh) return res.status(400).json({ error: "refresh token obrigatório" });

  try {
    const payload = jwt.verify(refresh, JWT_SECRET);
    const token = jwt.sign({ sub: payload.sub }, JWT_SECRET, { expiresIn: "15m" });
    res.json({ token });
  } catch {
    res.status(401).json({ error: "Refresh token inválido ou expirado" });
  }
});

// POST /auth/logout
app.post("/auth/logout", (_req, res) => {
  // Stateless: em produção invalidar o refresh token no banco
  res.status(204).send();
});

// GET /auth/me
app.get("/auth/me", (req, res) => {
  const auth = req.headers.authorization;
  if (!auth?.startsWith("Bearer "))
    return res.status(401).json({ error: "Token não fornecido" });

  try {
    const payload = jwt.verify(auth.slice(7), JWT_SECRET);
    res.json({ id: payload.sub, email: payload.email });
  } catch {
    res.status(401).json({ error: "Token inválido ou expirado" });
  }
});

app.listen(PORT, () => console.log(`chave-ms-auth rodando na porta ${PORT}`));
