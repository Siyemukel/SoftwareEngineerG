import { useState } from "react";
import { signInUser } from "../firebase/firebase.controllers.jsx";

const Login = () => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setSuccess("");
        
        try {
            const user = await signInUser(email, password);

            localStorage.setItem("token", user.accessToken);
            localStorage.setItem("uid", user.uid);
            localStorage.setItem("email", user.email);

            setSuccess("Login successful!");
            setEmail("");
            setPassword("");
        } catch (err) {
            setError("Login failed. Please try again.");
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-100 to-blue-300">
            <div className="bg-white shadow-lg rounded-lg p-8 w-full max-w-md">
                <h2 className="text-3xl font-bold mb-6 text-center text-blue-700">Login</h2>
                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block mb-1 font-medium text-gray-700">Email:</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                            placeholder="Enter your email"
                        />
                    </div>
                    <div>
                        <label className="block mb-1 font-medium text-gray-700">Password:</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                            placeholder="Enter your password"
                        />
                    </div>
                    <button
                        type="submit"
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded transition duration-200"
                    >
                        Login
                    </button>
                </form>
                {error && <p className="mt-4 text-center text-red-600">{error}</p>}
                {success && <p className="mt-4 text-center text-green-600">{success}</p>}
                <p>Don't have an account? <a href="/auth/signup" className="text-blue-500 hover:underline">Sign up</a></p>
            </div>
        </div>
    );
}

export default Login;
