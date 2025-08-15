import { useState } from "react";
import { useNavigate } from "react-router-dom";

const Login = () => {
    const [identifier, setIdentifier] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState("");
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage("");

        try {
            const res = await fetch("http://127.0.0.1:5000/api/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email: identifier.includes("@") ? identifier : undefined,
                    username: !identifier.includes("@") ? identifier : undefined,
                    password
                })
            });
            const data = await res.json();
            if (res.ok) {
                setMessage("Login successful!");

                localStorage.setItem("token", data.token);
                localStorage.setItem("uid", data.user.uid);
                localStorage.setItem("email", data.user.email);
                localStorage.setItem("username", data.user.username);
                
                setIdentifier("");
                setPassword("");

                setTimeout(() => navigate("/user/dashboard"), 1000);
            } else {
                setMessage(data.message || "Login failed. Please try again.");
            }
        } catch (err) {
            setMessage("Network error.");
        }
    };

    return (
        <>
            <h1>Signup</h1>
            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    required
                    placeholder="Enter your email or username"
                />
                <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    placeholder="Enter your password"
                />
                <button type="submit">Login</button>
            </form>
            {message && <p>{message}</p>}
        </>
    );
}

export default Login;
