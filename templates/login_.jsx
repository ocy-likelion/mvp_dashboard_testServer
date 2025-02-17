import React, { useState } from "react";
import styled from "styled-components";
import { proPage } from "../apis/api";

// 전체 화면 중앙 정렬
const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background-color: #ffff;
`;

// 로고 스타일
// const Logo = styled.img`
//   width: 300px;
//   height: 55px;
//   cursor: pointer;
//   margin-bottom: 20px;

//   @media (max-width: 768px) {
//     width: 120px; /* 모바일에서 로고 크기 조정 */
//     height: auto;
//   }
// `;

// 로그인 박스
const LoginBox = styled.div`
  width: 704px;
  height: 586px;
  border: 2px solid #dcdcdc;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
`;

// 로그인 텍스트
const LoginTitle = styled.h1`
  font-family: "SUITE", sans-serif;
  font-size: 50px;
  font-weight: bold;
  color: #ff7710;
  margin-bottom: 20px;
`;

// 입력창 스타일
const Input = styled.input`
  width: 490px;
  height: 55px;
  border: 2px solid #ff7710;
  font-size: 18px;
  padding: 10px;
  margin-bottom: 20px;
  border-radius: 10px;
  outline: none;

  &::placeholder {
    color: gray;
  }
`;

// 로그인 버튼
const LoginButton = styled.button`
  width: 515px;
  height: 80px;
  background-color: #ff7710;
  color: white;
  font-size: 20px;
  font-weight: bold;
  border: none;
  border-radius: 10px;
  cursor: pointer;

  &:hover {
    background-color: #e0660d;
  }
`;

const Login = () => {
  const [id, setId] = useState("");
  const [pw, setPw] = useState("");

  const handleLogin = async () => {
    const loginData = {
      password: pw,
      username: id,
    };

    try {
      const response = await proPage.postLogin(loginData);
      if (response?.status === 201) {
        alert("로그인 완료!");
      } else {
        console.error(response);
      }
    } catch (error) {
      console.error("Error posting comment:", error);
    }
  };

  const handleIdData = (e) => {
    setId(e.target.value);
  };

  const handlePwData = (e) => {
    setPw(e.target.value);
  };

  return (
    <Container>
      {/* 로고 (박스 밖) */}
      {/* <Logo src={process.env.PUBLIC_URL + "/likelion_logo.png"} alt="Logo" /> */}
      {/* 로그인 박스 */}
      <LoginBox>
        <LoginTitle>로그인</LoginTitle>

        {/* ID 입력창 */}
        <Input
          type="text"
          placeholder="ID를 입력해주세요(사번)"
          value={id}
          onChange={handleIdData}
        />

        {/* 비밀번호 입력창 */}
        <Input
          type="password"
          placeholder="비밀번호를 입력해주세요"
          value={pw}
          onChange={handlePwData}
        />

        {/* 로그인 버튼 */}
        <LoginButton onClick={() => handleLogin(id, pw)}>로그인</LoginButton>
      </LoginBox>
    </Container>
  );
};

export default Login;